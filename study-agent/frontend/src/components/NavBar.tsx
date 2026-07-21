import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Upload" },
  { to: "/documents", label: "Documents" },
  { to: "/graph", label: "Graph" },
  { to: "/schedule", label: "Schedule" },
  { to: "/export", label: "Export" },
  { to: "/settings", label: "Settings" },
];

export function NavBar() {
  return (
    <nav className="navbar">
      {links.map((l) => (
        <NavLink key={l.to} to={l.to} end={l.to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
          {l.label}
        </NavLink>
      ))}
    </nav>
  );
}
