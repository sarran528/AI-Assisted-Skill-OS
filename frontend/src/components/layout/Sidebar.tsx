import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import React from "react";
import { useNavigationStore } from "../../store/navigationStore";
import { useAssessmentStore, GAME_IDS } from "../../stores/assessmentStore";

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
        to={to}
        onClick={(event) => {
          if (locked) event.preventDefault();
        }}
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
    const { user, clearAuth } = useAuthStore();
    const {
      profileState,
      currentSkill,
      roadmapState,
      resetNavigation,
    } = useNavigationStore();
    const { games } = useAssessmentStore();

    const completedLevels = GAME_IDS.filter(id => games[id].completed).length;
    const isAssessmentComplete = completedLevels === 6;
    const isProfileLocked = false;
    const isSkillsLocked = !profileState.isActive;
    const isRoadmapLocked = false;

    const handleLogout = () => {
        resetNavigation();
        clearAuth();
        window.location.href = "/login";
    };

  return (
    <aside className="sidebar">
        <div className="sidebar__header">
            <h2 className="sidebar__title">SkillOS</h2>
        </div>
        <nav className="sidebar__nav">
            <ul>
                <SidebarItem to="/profile" label="Profile" />
                <SidebarItem
                    to="/assessment"
                    label="Assessment"
                    state={isAssessmentComplete ? "Complete" : `${completedLevels} / 6 complete`}
                />
                <SidebarItem
                    to="/skill/select"
                    label="Skills"
                    state={isSkillsLocked ? "Locked" : currentSkill.skillName || "No skill selected"}
                    locked={isSkillsLocked}
                    tooltip="Activate your profile to unlock."
                />
                <SidebarItem
                    to="/roadmap"
                    label="Roadmap"
                    state={
                      !currentSkill.skillId
                        ? "Locked"
                        : roadmapState.isGenerating
                          ? "Generating..."
                          : roadmapState.roadmapComplete
                            ? "Complete"
                            : roadmapState.currentPhase
                              ? `${roadmapState.currentPhase} — active`
                              : "Locked"
                    }
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
