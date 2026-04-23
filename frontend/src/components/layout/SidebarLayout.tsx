import { ReactNode } from 'react';
import Sidebar from './RevisedSidebar';

interface SidebarLayoutProps {
  children: ReactNode;
}

export function SidebarLayout({ children }: SidebarLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar - Fixed Position */}
      <Sidebar />
      
      {/* Main Content Area - Full Width with Sidebar Offset */}
      <main className="ml-[220px]">
        {children}
      </main>
    </div>
  );
}
