import { useEffect, useState } from "react";
import { getPrincipal, LOGIN_URL, LOGOUT_URL, OWNER_ROLE, type ClientPrincipal } from "./api/auth";
import { Header } from "./components/Header";
import { SystemCheck } from "./components/SystemCheck";

type AuthState = { status: "loading" } | { status: "ready"; principal: ClientPrincipal | null };

export default function App() {
  const [auth, setAuth] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    void getPrincipal().then((principal) => setAuth({ status: "ready", principal }));
  }, []);

  const principal = auth.status === "ready" ? auth.principal : null;

  return (
    <div className="app">
      <div className="spectrum" aria-hidden />
      <Header principal={principal} />
      <main className="main">
        {auth.status === "loading" && <p className="muted">Loading…</p>}

        {auth.status === "ready" && !principal && (
          <section className="card center">
            <h1>Welcome to Prism</h1>
            <p className="muted">Sign in with your Microsoft account to continue.</p>
            <a className="btn" href={LOGIN_URL}>
              Sign in with Microsoft
            </a>
          </section>
        )}

        {principal && !principal.userRoles.includes(OWNER_ROLE) && (
          <section className="card center">
            <h1>This account can't use Prism</h1>
            <p className="muted">
              {principal.userDetails} hasn't been invited. Sign out and use the invited account.
            </p>
            <a className="btn" href={LOGOUT_URL}>
              Sign out
            </a>
          </section>
        )}

        {principal?.userRoles.includes(OWNER_ROLE) && (
          <>
            <section className="intro">
              <h1>Turn videos into transcripts, summaries and action plans.</h1>
              <p className="muted">
                Foundation is in place. Upload transcription arrives in M1 and YouTube links in M2.
              </p>
            </section>
            <SystemCheck />
          </>
        )}
      </main>
    </div>
  );
}
