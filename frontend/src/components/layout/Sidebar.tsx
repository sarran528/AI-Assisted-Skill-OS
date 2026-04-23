import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import React from "react";

// --- SidebarItem Component ---
interface SidebarItemProps {
  to: string;
  label: string;
  state?: string;
  locked?: boolean;
  tooltip?: string;
}

const SidebarItem: React.FC<SidebarItemProps> = ({ to, label, state, locked, tooltip }) => {
  return (
    <li title={locked ? tooltip : undefined}>
      <NavLink
        to={locked ? "#" : to}
        className={({ isActive }) =>
          "nav-item " +
          (isActive && !locked ? "nav-item--active " : "") +
          (locked ? "nav-item--locked" : "")
        }
      >
        <span className="nav-item__label">{label}</span>
        {state && <span className="nav-item__state">{state}</span>}
      </NavLink>
    </li>
  );
};


// --- Main Sidebar Component ---
export function Sidebar() {
    // Mock data based on user feedback/snippets
    const completedLevels = 0; // "0 / 6"
    const isProfileLocked = true; // "Locked"
    const profileState = { isActive: false };
    const isSkillsLocked = true; // "Locked"
    const currentSkill = { skillName: "", skillId: "" };
    const isRoadmapLocked = true; // "Locked"
    const roadmapState = { currentPhase: "" };

    const { user, clearAuth } = useAuthStore();

    const handleLogout = () => {
        clearAuth();
        window.location.href = "/";
    };

  return (
    <aside className="sidebar">
        <div className="sidebar__header">
            <h2 className="sidebar__title">SkillOS</h2>
        </div>
        <nav className="sidebar__nav">
            <ul>
                <SidebarItem to="/dashboard" label="Dashboard" />
                <SidebarItem
                    to="/assessment"
                    label="Assessment"
                    state={`${completedLevels} / 6 complete`}
                />
                <SidebarItem
                    to="/profile"
                    label="Profile"
                    state={isProfileLocked ? "Locked" : profileState.isActive ? "Active" : "Inactive"}
                    locked={isProfileLocked}
                    tooltip="Complete all 6 assessments to unlock."
                />
                <SidebarItem
                    to="/skill/select"
                    label="Skills"
                    state={isSkillsLocked ? "Locked" : currentSkill.skillName || "No skill selected"}
                    locked={isSkillsLocked}
                    tooltip="Activate your profile to unlock."
                />
                <SidebarItem
                    to={`/roadmap/${currentSkill.skillId || ''}`}
                    label="Roadmap"
                    state={isRoadmapLocked ? "Locked" : roadmapState.currentPhase ? `${roadmapState.currentPhase} — active` : "Roadmap generated"}
                    locked={isRoadmapLocked}
                    tooltip="Select a skill and generate a roadmap to unlock."
                />
                <SidebarItem
                    to="/resources"
                    label="Resources"
                    state={roadmapState.currentPhase ? `Showing ${roadmapState.currentPhase} content` : "No active phase"}
                />
                <SidebarItem to="/help" label="Help" />
            </ul>
        </nav>
        <div className="sidebar-footer">
            <p className="sidebar-footer__email">{user?.email}</p>
            <button onClick={handleLogout} className="brutal-button brutal-button--secondary">
            Logout
            </button>
        </div>
    </aside>
  );
}
