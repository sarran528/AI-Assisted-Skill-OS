import React from "react";
import { NavLink } from "react-router-dom";
import { useAuthStore } from "../../store/authStore";
import { useNavigationStore } from "../../store/navigationStore";

const Sidebar = () => {
  const { user, clearAuth } = useAuthStore();
  const { assessmentProgress, profileState, currentSkill, roadmapState } = useNavigationStore();

  const handleLogout = () => {
    clearAuth();
    window.location.href = "/login";
  };

  const completedLevels = Object.values(assessmentProgress)
    .filter(level => level.status === 'complete').length;
  
  const isProfileLocked = completedLevels < 6;
  const isSkillsLocked = !profileState.isActive;
  const isRoadmapLocked = !currentSkill.skillId || !roadmapState.isGenerated;

  return (
    <div className="fixed left-0 top-0 h-full w-[220px] bg-gray-100 shadow-md flex flex-col justify-between">
      {/* Header */}
      <div className="p-4 border-b border-gray-300">
        <h1 className="text-xl font-bold">SkillOS</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1">
        <ul className="space-y-2 p-4">
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
          <SidebarItem to="/doubt" label="Help" />
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-300">
        <p className="text-sm text-gray-600">{user?.email || 'user@example.com'}</p>
        <button
          onClick={handleLogout}
          className="mt-2 w-full bg-red-500 text-white py-2 rounded hover:bg-red-600"
        >
          Logout
        </button>
      </div>
    </div>
  );
};

const SidebarItem = ({ to, label, state, locked, tooltip }: any) => {
  return (
    <li>
      <NavLink
        to={locked ? "#" : to}
        className={({ isActive }) =>
          `flex items-center space-x-2 p-2 rounded ${
            isActive ? "bg-yellow-300 text-black" : "text-gray-700"
          } ${locked ? "cursor-not-allowed text-gray-400" : "hover:bg-gray-200"}`
        }
        title={locked ? tooltip : ""}
      >
        <span className="material-icons">chevron_right</span>
        <span>{label}</span>
      </NavLink>
      {state && <p className="text-xs text-gray-500 ml-8">{state}</p>}
    </li>
  );
};

export default Sidebar;
