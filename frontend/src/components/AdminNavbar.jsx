import { Link, useLocation } from "react-router-dom";

const navStyle = {
  display: "flex",
  alignItems: "center",
  gap: 4,
};

const linkStyle = (active) => ({
  padding: "6px 14px",
  borderRadius: 6,
  textDecoration: "none",
  fontSize: 13,
  fontWeight: 600,
  color: active ? "#fff" : "#a0a0c0",
  background: active ? "#2a2a4a" : "transparent",
  transition: "background 0.15s, color 0.15s",
  whiteSpace: "nowrap",
});

export default function AdminNavbar() {
  const location = useLocation();
  const isMap = location?.pathname === "/";
  const isAdmin = location?.pathname === "/admin";

  return (
    <nav style={navStyle}>
      <Link to="/" style={linkStyle(isMap)}>
        🗺️ Mappa
      </Link>
      <Link to="/admin" style={linkStyle(isAdmin)}>
        ⚙️ Admin
      </Link>
    </nav>
  );
}
