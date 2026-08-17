import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { ViewerHome } from './viewer/ViewerHome';
import { ShowsPage } from './cms/ShowsPage';
import { PublishPage } from './cms/PublishPage';

export const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#0f1015] flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Routes>
          {/* Viewer Surface */}
          <Route path="/" element={<ViewerHome />} />
          <Route path="/viewer" element={<ViewerHome />} />

          {/* CMS Surface */}
          <Route path="/cms" element={<ShowsPage />} />
          <Route path="/cms/publish" element={<PublishPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};
