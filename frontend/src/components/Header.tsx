import { LOGOUT_URL, type ClientPrincipal } from "../api/auth";

export function Header({ principal }: { principal: ClientPrincipal | null }) {
  return (
    <header className="header">
      <div className="brand">
        <img src="/favicon.svg" alt="" width={28} height={28} />
        <div>
          <span className="brand-name">Prism</span>
          <span className="brand-by">by Kaleidoscope</span>
        </div>
      </div>
      {principal && (
        <div className="user">
          <span className="user-name" title={principal.userDetails}>
            {principal.userDetails}
          </span>
          <a className="link" href={LOGOUT_URL}>
            Sign out
          </a>
        </div>
      )}
    </header>
  );
}
