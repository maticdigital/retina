import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { Report } from './pages/Report';
import { LensDetail } from './pages/LensDetail';
import { Profile } from './pages/Profile';
import { Admin } from './pages/Admin';
import ProjectStatus from './pages/ProjectStatus';
import { SharedReport } from './pages/SharedReport';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/shared/:token" element={<SharedReport />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><Admin /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/projects/:projectId/status" element={<ProtectedRoute><ProjectStatus /></ProtectedRoute>} />
          <Route path="/projects/:projectId" element={<ProtectedRoute><Report /></ProtectedRoute>} />
          <Route path="/projects/:projectId/lens/:lensId" element={<ProtectedRoute><LensDetail /></ProtectedRoute>} />
          <Route path="/report/:projectId" element={<ProtectedRoute><Report /></ProtectedRoute>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
