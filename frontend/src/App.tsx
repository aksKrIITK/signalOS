import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { DashboardPage } from './pages/DashboardPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { LeadsPage } from './pages/LeadsPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { AgentTracesPage } from './pages/AgentTracesPage';
import { KnowledgePage } from './pages/KnowledgePage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-dark-900 overflow-hidden font-sans text-slate-100">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto">
            <Routes>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/leads" element={<LeadsPage />} />
              <Route path="/approvals" element={<ApprovalsPage />} />
              <Route path="/traces" element={<AgentTracesPage />} />
              <Route path="/knowledge" element={<KnowledgePage />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};
