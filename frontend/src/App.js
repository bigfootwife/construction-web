import { BrowserRouter, HashRouter, Routes, Route, useLocation } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import "./App.css";
import { AuthProvider } from "./context/AuthContext";
import { ConfirmProvider } from "./hooks/useConfirm";
import { Toaster } from "sonner";
import Header from "./components/Header";
import Footer from "./components/Footer";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/Home";
import Services from "./pages/Services";
import Portfolio from "./pages/Portfolio";
import ProjectDetail from "./pages/ProjectDetail";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Admin from "./pages/Admin";
import AuthCallback from "./pages/AuthCallback";
import { STATIC_MODE } from "./lib/dataLayer";

const Router = STATIC_MODE ? HashRouter : BrowserRouter;

function AppRouter() {
  const location = useLocation();
  // Handle Emergent OAuth callback synchronously (only when backend is on)
  if (!STATIC_MODE && location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/services" element={<Services />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/portfolio/:id" element={<ProjectDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/contact" element={<Contact />} />
          {!STATIC_MODE && <Route path="/login" element={<Login />} />}
          {!STATIC_MODE && <Route path="/register" element={<Register />} />}
          {!STATIC_MODE && (
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
          )}
          {!STATIC_MODE && (
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <Admin />
                </ProtectedRoute>
              }
            />
          )}
        </Routes>
      </main>
      <Footer />
    </>
  );
}

export default function App() {
  return (
    <div className="App">
      <HelmetProvider>
        <AuthProvider>
          <Router>
            <ConfirmProvider>
              <AppRouter />
              <Toaster position="top-right" richColors />
            </ConfirmProvider>
          </Router>
        </AuthProvider>
      </HelmetProvider>
    </div>
  );
}
