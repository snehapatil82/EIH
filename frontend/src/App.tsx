import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Repository } from './types/repository';
import { repositoryService } from './services/repositoryService';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { RepositoriesPage } from './pages/RepositoriesPage';
import { ExplorerPage } from './pages/ExplorerPage';
import { ChatPage } from './pages/ChatPage';
import { EngineeringTaskPage } from './pages/EngineeringTaskPage';
import { ArchitecturePage } from './pages/ArchitecturePage';
import { DocumentationPage } from './pages/DocumentationPage';

export const App: React.FC = () => {

  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSelectRepo = (repo: Repository) => {
    setSelectedRepo(repo);
    try {
      localStorage.setItem('eih_selected_repo_id', repo.id);
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }
  };

  const fetchRepositories = async () => {
    setIsLoading(true);
    try {
      const data = await repositoryService.list();
      setRepositories(data);
      if (data.length > 0) {
        const savedId = localStorage.getItem('eih_selected_repo_id');
        const matched = savedId ? data.find((r) => r.id === savedId) : null;
        const current = matched || data[0];
        setSelectedRepo(current);
        localStorage.setItem('eih_selected_repo_id', current.id);
      }
    } catch (err) {
      console.error('Failed to fetch repositories:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRepositories();
  }, []);

  const handleConnectRepo = async (url: string, branch?: string) => {
    setIsLoading(true);
    try {
      const newRepo = await repositoryService.connect(url, branch);
      setRepositories((prev) => [newRepo, ...prev.filter((r) => r.id !== newRepo.id)]);
      handleSelectRepo(newRepo);
    } catch (err) {
      console.error('Error connecting repo:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
        <Navbar
          repositories={repositories}
          selectedRepo={selectedRepo}
          onSelectRepo={handleSelectRepo}
        />

        <div className="flex flex-1 overflow-hidden">
          <Sidebar />

          <main className="flex-1 overflow-y-auto bg-slate-950/50">
            <Routes>
              <Route
                path="/"
                element={
                  <DashboardPage
                    repositories={repositories}
                    selectedRepo={selectedRepo}
                    onSelectRepo={handleSelectRepo}
                    onConnectRepo={handleConnectRepo}
                    isLoading={isLoading}
                  />
                }
              />
              <Route
                path="/repositories"
                element={
                  <RepositoriesPage
                    repositories={repositories}
                    selectedRepo={selectedRepo}
                    onSelectRepo={handleSelectRepo}
                    onConnectRepo={handleConnectRepo}
                    isLoading={isLoading}
                    onRefresh={fetchRepositories}
                  />
                }
              />
              <Route
                path="/explorer"
                element={<ExplorerPage selectedRepo={selectedRepo} />}
              />
              <Route
                path="/chat"
                element={<ChatPage selectedRepo={selectedRepo} />}
              />
              <Route
                path="/tasks"
                element={<EngineeringTaskPage selectedRepo={selectedRepo} />}
              />
              <Route
                path="/architecture"
                element={<ArchitecturePage selectedRepo={selectedRepo} />}
              />
              <Route
                path="/documentation"
                element={<DocumentationPage selectedRepo={selectedRepo} />}
              />

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
};

export default App;
