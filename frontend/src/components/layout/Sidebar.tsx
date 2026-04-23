import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";

export function Sidebar() {
  const { user, clearAuth } = useAuthStore();

  const handleLogout = () => {
    clearAuth();
    window.location.href = "/";
  };

  return (
    <aside className="sidebar">
      <h2 className="sidebar__title">SkillOS</h2>
      <nav>
        <div className="nav-group">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
            Dashboard
          </NavLink>
          <NavLink to="/assessment" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
            Assessment
          </NavLink>
        </div>
        <NavLink to="/profile" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
          Profile
        </NavLink>
        <NavLink to="/skill/select" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
          Skills
        </NavLink>
        <NavLink to="/roadmap" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
          Roadmap
        </NavLink>
        <NavLink to="/resources" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
          Resources
        </NavLink>
        <NavLink to="/help" className={({ isActive }) => `nav-item ${isActive ? "nav-item--active" : ""}`}>
          Help
        </NavLink>
      </nav>
      <div className="sidebar-footer">
        <p>{user?.email}</p>
        <button onClick={handleLogout} className="brutal-button brutal-button--secondary">
          Logout
        </button>
      </div>
    </aside>
  );
}
