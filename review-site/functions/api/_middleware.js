// Authentication for every /api/* route.
//
// Cloudflare Access sits in front of this site and will not let an unapproved
// visitor reach it at all. This middleware does NOT trust that. Access is
// configured per-hostname, and a Pages project answers on its own
// *.pages.dev deployment URLs as well as the custom domain — miss one in the
// Access policy and the API is open to the internet while the site looks
// protected. So the token is verified here, on every request, independently.
//
// It fails CLOSED. If the Access variables are unset, the API returns 503 and
// serves nothing. The tempting alternative — "no auth configured, so allow
// everything" — is how an internal review board ends up world-readable.

const JWKS_TTL_MS = 60 * 60 * 1000;

// Per-isolate cache. Isolates are short-lived and there may be many, so this is
// a courtesy to the certs endpoint, not something correctness depends on.
let jwksCache = { url: null, fetchedAt: 0, keys: null };

function json(status, obj) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'no-store',
    },
  });
}

function b64urlToBytes(s) {
  const padded = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
  const bin = atob(padded);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function decodeSegment(seg) {
  return JSON.parse(new TextDecoder().decode(b64urlToBytes(seg)));
}

async function getSigningKeys(teamDomain) {
  const url = `https://${teamDomain}/cdn-cgi/access/certs`;
  const now = Date.now();
  if (jwksCache.keys && jwksCache.url === url && now - jwksCache.fetchedAt < JWKS_TTL_MS) {
    return jwksCache.keys;
  }
  const resp = await fetch(url, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!resp.ok) throw new Error(`could not fetch Access signing keys (${resp.status})`);
  const body = await resp.json();
  const keys = Array.isArray(body.keys) ? body.keys : [];
  if (keys.length === 0) throw new Error('Access signing key set was empty');
  jwksCache = { url, fetchedAt: now, keys };
  return keys;
}

// Returns the verified email address, or throws. Never returns a value derived
// from anything the caller controls without a signature check first.
async function verifyAccessJwt(token, teamDomain, expectedAud) {
  const parts = token.split('.');
  if (parts.length !== 3) throw new Error('malformed token');
  const [headerB64, payloadB64, sigB64] = parts;

  const header = decodeSegment(headerB64);
  if (header.alg !== 'RS256') throw new Error(`unexpected signing algorithm: ${header.alg}`);
  if (!header.kid) throw new Error('token has no key id');

  const keys = await getSigningKeys(teamDomain);
  const jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) throw new Error('token signed by an unknown key');

  const key = await crypto.subtle.importKey(
    'jwk',
    { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: 'RS256', ext: true },
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['verify'],
  );
  const signed = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
  const ok = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, b64urlToBytes(sigB64), signed);
  if (!ok) throw new Error('signature did not verify');

  const claims = decodeSegment(payloadB64);
  const now = Math.floor(Date.now() / 1000);
  const SKEW = 60;

  if (typeof claims.exp !== 'number' || claims.exp + SKEW <= now) throw new Error('token expired');
  if (typeof claims.nbf === 'number' && claims.nbf - SKEW > now) throw new Error('token not yet valid');
  if (typeof claims.iat === 'number' && claims.iat - SKEW > now) throw new Error('token issued in the future');

  // The audience tag is what ties this token to THIS Access application. Without
  // it, a valid token for any other app in the same Cloudflare team would be
  // accepted here.
  const aud = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!aud.includes(expectedAud)) throw new Error('token was issued for a different application');
  if (claims.iss !== `https://${teamDomain}`) throw new Error('token was issued by a different team');

  const email = String(claims.email || claims.common_name || '').trim().toLowerCase();
  if (!email) throw new Error('token carries no identity');
  return email;
}

function readToken(request) {
  const header = request.headers.get('Cf-Access-Jwt-Assertion');
  if (header) return header;
  // Fallback for same-origin fetches where the header is not forwarded.
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
  return match ? match[1] : null;
}

export async function onRequest(context) {
  const { request, env, next, data } = context;

  const teamDomain = (env.ACCESS_TEAM_DOMAIN || '').trim().replace(/^https?:\/\//, '').replace(/\/+$/, '');
  const expectedAud = (env.ACCESS_AUD || '').trim();

  let email = null;

  if (teamDomain && expectedAud) {
    const token = readToken(request);
    if (!token) {
      return json(401, { error: 'Not signed in. Reload the page to sign in again.' });
    }
    try {
      email = await verifyAccessJwt(token, teamDomain, expectedAud);
    } catch (err) {
      return json(401, { error: 'Sign-in could not be verified.', detail: String(err.message || err) });
    }
  } else if (env.ALLOW_DEV_AUTH === '1' && env.DEV_REVIEWER_EMAIL) {
    // Local development only. Unreachable in production, where the two Access
    // variables above are always set and take this branch out of play.
    email = String(env.DEV_REVIEWER_EMAIL).trim().toLowerCase();
  } else {
    return json(503, {
      error: 'This review site is not finished being set up, so it is refusing to show anything.',
      detail: 'ACCESS_TEAM_DOMAIN and ACCESS_AUD are not both configured. See DEPLOY.md.',
    });
  }

  const owners = String(env.OWNER_EMAILS || '')
    .toLowerCase()
    .split(/[,\s]+/)
    .filter(Boolean);

  data.email = email;
  data.isOwner = owners.includes(email);

  const response = await next();
  // Review state is per-person-visible and changes constantly; never let an
  // intermediary hold on to it.
  response.headers.set('cache-control', 'no-store');
  return response;
}
