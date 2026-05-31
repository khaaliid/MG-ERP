import { useEffect, useRef, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Inventory from './pages/Inventory';
import POS from './pages/POS';
import Ledger from './pages/Ledger';
import Reports from './pages/Reports';
import Expenses from './pages/Expenses';
import TransactionsHistory from './pages/TransactionsHistory';
import Users from './pages/Users';
import SalesUsers from './pages/SalesUsers';
import SalesUserReport from './pages/SalesUserReport';
import './App.css';
import { useTranslation } from 'react-i18next';
import './i18n';
import LanguageSelector from './components/LanguageSelector';
import { APP_CONFIG } from './config';

type RemoteAd = {
  title: string;
  description: string;
  url: string;
};

const normalizeAdResponse = (payload: any): RemoteAd => {
  const adSource = Array.isArray(payload?.ads)
    ? payload.ads[0]
    : Array.isArray(payload?.posts)
      ? payload.posts[0]
      : payload;

  return {
    title: adSource?.title || adSource?.name || 'Sponsored',
    description: adSource?.description || adSource?.body || 'Check out our latest offer.',
    url: adSource?.url || adSource?.link || '#'
  };
};

const FALLBACK_SLIDES = [
  {
    title: 'Place your ad here',
    description: 'This space is available for sponsored campaigns and product promotions.'
  },
  {
    title: 'Place your ad here',
    description: 'Reach operators and managers directly inside their daily ERP workflow.'
  },
  {
    title: 'Place your ad here',
    description: 'Display your brand message with a clean, high-visibility placement.'
  }
];

const FallbackAdCarousel = () => {
  const [activeSlide, setActiveSlide] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % FALLBACK_SLIDES.length);
    }, 3500);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className="fallback-ad-carousel" aria-label="Fallback ad carousel">
      <div className="fallback-ad-track" style={{ transform: `translateX(-${activeSlide * 100}%)` }}>
        {FALLBACK_SLIDES.map((slide, index) => (
          <div className="fallback-ad-slide" key={`${slide.title}-${index}`}>
            <div className="fallback-ad-badge">Ad Placeholder</div>
            <h4>{slide.title}</h4>
            <p>{slide.description}</p>
          </div>
        ))}
      </div>
      <div className="fallback-ad-dots" aria-hidden="true">
        {FALLBACK_SLIDES.map((_, index) => (
          <button
            key={index}
            type="button"
            className={`fallback-ad-dot${index === activeSlide ? ' active' : ''}`}
            onClick={() => setActiveSlide(index)}
          />
        ))}
      </div>
    </div>
  );
};

const AdSlot = () => {
  const [remoteAd, setRemoteAd] = useState<RemoteAd | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdsApiFailed, setIsAdsApiFailed] = useState(false);
  const [isAdsenseFailed, setIsAdsenseFailed] = useState(false);
  const adsenseSlotRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const adsApiUrl = APP_CONFIG.ads.publicAdsApiUrl;

    const loadAd = async () => {
      try {
        setIsLoading(true);
        setIsAdsApiFailed(false);

        const response = await fetch(adsApiUrl, {
          method: 'GET',
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch ad: ${response.status}`);
        }

        const payload = await response.json();
        setRemoteAd(normalizeAdResponse(payload));
      } catch (fetchError: any) {
        if (fetchError?.name !== 'AbortError') {
          setIsAdsApiFailed(true);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadAd();

    return () => {
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const slotNode = adsenseSlotRef.current;
      if (!slotNode) {
        setIsAdsenseFailed(true);
        return;
      }

      const hasAdsenseScript = !!document.querySelector('script[src*="adsbygoogle"]');
      const hasAdsenseRuntime = typeof (window as any).adsbygoogle !== 'undefined';
      const hasRenderedAd = !!slotNode.querySelector('iframe, ins, img, object, embed');

      if ((!hasAdsenseScript && !hasAdsenseRuntime) || !hasRenderedAd) {
        setIsAdsenseFailed(true);
      }
    }, 4000);

    return () => {
      window.clearTimeout(timer);
    };
  }, []);

  if (isAdsApiFailed || isAdsenseFailed) {
    return <FallbackAdCarousel />;
  }

  return (
    <div className="common-ad-column">
      <div
        id="light-adsense-ad-slot"
        className="common-ad-slot common-ad-slot-adsense"
        data-ad-slot="light-global-adsense"
        data-ad-provider="adsense"
        ref={adsenseSlotRef}
        style={{ flex: 1, overflow: 'hidden' }}
      />
      <div
        id="light-backend-ad-slot"
        className="common-ad-slot common-ad-slot-backend"
        data-ad-slot="light-global-backend"
        data-ad-provider="backend-api"
        style={{ flex: 1, overflow: 'hidden' }}
      >
        {isLoading && <p>Loading ad...</p>}
        {!isLoading && remoteAd && (
          <>
            <h4 style={{ marginTop: 0 }}>{remoteAd.title}</h4>
            <p>{remoteAd.description}</p>
            {remoteAd.url !== '#' && (
              <a href={remoteAd.url} target="_blank" rel="noopener noreferrer">
                Learn more
              </a>
            )}
          </>
        )}
      </div>
    </div>
  );
};

function MainApp() {
  const [activeMenu, setActiveMenu] = useState('pos');
  const { user, logout, hasRole } = useAuth();
  const { t, i18n } = useTranslation();
  console.log("Current detected language:", i18n.language);

  const handleLogout = () => {
    if (confirm('Are you sure you want to logout?')) {
      logout();
    }
  };

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h2>{t('app_name')}</h2>
          {user && (
            <div style={{
              fontSize: '12px',
              color: '#7f8c8d',
              marginTop: '5px'
            }}>
              <div>{user.full_name || user.username}</div>
              <div style={{ color: '#3498db', textTransform: 'capitalize' }}>
                {user.role.toLowerCase().replace('_', ' ')}
              </div>
            </div>
          )}
          <LanguageSelector />
        </div>
        <ul className="nav-menu">
          {hasRole('manager', 'super_admin') && (
          <li className={activeMenu === 'dashboard' ? 'active' : ''}>
            <Link to="/dashboard" onClick={() => setActiveMenu('dashboard')}>
              📊 {t('dashboard_title')}
            </Link>
          </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'inventory' ? 'active' : ''}>
              <Link to="/inventory" onClick={() => setActiveMenu('inventory')}>
                📦 {t('inventory_title')}
              </Link>
            </li>
          )}
          <li className={activeMenu === 'pos' ? 'active' : ''}>
            <Link to="/pos" onClick={() => setActiveMenu('pos')}>
              🛒 {t('pos_title')}
            </Link>
          </li>
          <li className={activeMenu === 'transactions-history' ? 'active' : ''}>
            <Link to="/transactions-history" onClick={() => setActiveMenu('transactions-history')}>
              🧾 {t('transactions_history_title')}
            </Link>
          </li>
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'ledger' ? 'active' : ''}>
              <Link to="/ledger" onClick={() => setActiveMenu('ledger')}>
                📝 {t('ledger_title')}
              </Link>
            </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'expenses' ? 'active' : ''}>
              <Link to="/expenses" onClick={() => setActiveMenu('expenses')}>
                💰 {t('expenses_title')}
              </Link>
            </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'auth-users' ? 'active' : ''}>
              <Link to="/auth-users" onClick={() => setActiveMenu('auth-users')}>
                🔐 {t('user_management_title')}
              </Link>
            </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'sales-users' ? 'active' : ''}>
              <Link to="/sales-users" onClick={() => setActiveMenu('sales-users')}>
                👥 {t('sales_users_title')}
              </Link>
            </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'reports' ? 'active' : ''}>
              <Link to="/reports" onClick={() => setActiveMenu('reports')}>
                📈 {t('reports_title')}
              </Link>
            </li>
          )}
          {hasRole('manager', 'super_admin') && (
            <li className={activeMenu === 'sales-user-report' ? 'active' : ''}>
              <Link to="/sales-user-report" onClick={() => setActiveMenu('sales-user-report')}>
                👤 {t('sales_user_report_title')}
              </Link>
            </li>
          )}
          <li>
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault();
                handleLogout();
              }}
              style={{ color: '#e74c3c' }}
            >
              🚪 Logout
            </a>
          </li>
        </ul>
      </nav>

      <div className="content-wrapper">
        <main className="main-content">
          <Routes>
            <Route path="/" element={
              <ProtectedRoute>
                <POS />
              </ProtectedRoute>
            } />
            <Route path="/dashboard" element={
              <ProtectedRoute requiredRole="manager">
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/inventory" element={
              <ProtectedRoute requiredRole="manager">
                <Inventory />
              </ProtectedRoute>
            } />
            <Route path="/pos" element={
              <ProtectedRoute>
                <POS />
              </ProtectedRoute>
            } />
            <Route path="/transactions-history" element={
              <ProtectedRoute>
                <TransactionsHistory />
              </ProtectedRoute>
            } />
            <Route path="/ledger" element={
              <ProtectedRoute requiredRole="manager">
                <Ledger />
              </ProtectedRoute>
            } />
            <Route path="/expenses" element={
              <ProtectedRoute requiredRole="manager">
                <Expenses />
              </ProtectedRoute>
            } />
            <Route path="/auth-users" element={
              <ProtectedRoute requiredRole="super_admin">
                <Users />
              </ProtectedRoute>
            } />
            <Route path="/sales-users" element={
              <ProtectedRoute requiredRole="manager">
                <SalesUsers />
              </ProtectedRoute>
            } />
            <Route path="/reports" element={
              <ProtectedRoute requiredRole="manager">
                <Reports />
              </ProtectedRoute>
            } />
            <Route path="/sales-user-report" element={
              <ProtectedRoute requiredRole="manager">
                <SalesUserReport />
              </ProtectedRoute>
            } />
          </Routes>
        </main>
        <AdSlot />
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={
            <div className="app">
              <div className="content-wrapper">
                <main className="main-content">
                  <Login />
                </main>
                <AdSlot />
              </div>
            </div>
          } />
          <Route path="/*" element={<MainApp />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
