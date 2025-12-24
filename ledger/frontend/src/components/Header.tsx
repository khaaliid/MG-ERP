import React, { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import LanguageSwitcher from './LanguageSwitcher';
import '../assets/Navbar.css';

interface HeaderProps {
  currentPage?: string;
}

const Header: React.FC<HeaderProps> = ({ currentPage = 'transactions' }) => {
  const [showReportsMenu, setShowReportsMenu] = useState(false);
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const dropdownRef = useRef<HTMLLIElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowReportsMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleReportsMenu = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault();
    setShowReportsMenu((prev) => !prev);
  };

  const reports = [
    { id: 'trial-balance', name: t('nav_trial_balance'), href: '/reports/trial-balance' },
    { id: 'balance-sheet', name: t('nav_balance_sheet'), href: '/reports/balance-sheet' },
    { id: 'income-statement', name: t('nav_income_statement'), href: '/reports/income-statement' },
    { id: 'general-ledger', name: t('nav_general_ledger'), href: '/reports/general-ledger' },
    { id: 'cash-flow', name: t('nav_cash_flow'), href: '/reports/cash-flow' },
    { id: 'dashboard', name: t('nav_dashboard'), href: '/reports/dashboard' },
    { id: 'aging', name: t('nav_aging_report'), href: '/reports/aging' },
  ];

  const navigationItems = [
    { key: 'transactions', name: t('nav_transactions'), href: '/', active: currentPage === 'transactions' },
    { key: 'accounts', name: t('nav_accounts'), href: '/accounts', active: currentPage === 'accounts' },
    { key: 'reports', name: t('nav_reports'), href: '/reports', isDropdown: true, items: reports, active: currentPage === 'reports' },
  ];

  return (
    <header>
      <nav className="navbar">
        <div className="navbar-left">
          <a href="/" className="logo">
            {t('app_title')}
          </a>
        </div>

        <div className="navbar-center">
          <ul className="nav-links">
            {navigationItems.map((item) => {
              if (!item.isDropdown) {
                return (
                  <li key={item.key}>
                    <a href={item.href} className={item.active ? 'active' : undefined}>
                      {item.name}
                    </a>
                  </li>
                );
              }

              return (
                <li key={item.key} className="dropdown" ref={dropdownRef}>
                  <a
                    href={item.href}
                    onClick={toggleReportsMenu}
                    className={`dropdown-toggle ${showReportsMenu || item.active ? 'active' : ''}`.trim()}
                    aria-haspopup="true"
                    aria-expanded={showReportsMenu}
                  >
                    <span>{item.name}</span>
                    <span className="caret">▼</span>
                  </a>

                  {showReportsMenu && (
                    <ul className="dropdown-menu">
                      {item.items?.map((report) => (
                        <li key={report.id}>
                          <a
                            href={report.href}
                            className="dropdown-link"
                            onClick={() => setShowReportsMenu(false)}
                          >
                            {report.name}
                          </a>
                        </li>
                      ))}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </div>

        <div className="navbar-right">
          <LanguageSwitcher />
          <div className="user-meta">
            <span className="user-name">{user?.username}</span>
            <button onClick={logout} className="logout-button">
              {t('logout')}
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Header;