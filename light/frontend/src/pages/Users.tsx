import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { authAPI } from '../api';
import { useAuth } from '../AuthContext';
import '../i18n';

interface User {
  id: number;
  username: string;
  email?: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

function Users() {
  const { t } = useTranslation();
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    role: 'cashier',
    is_active: true,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchUsers();
  }, [showInactive]);

  const fetchUsers = async () => {
    try {
      const response = await authAPI.getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      alert(t('users_load_failed'));
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = t('users_username_required');
    } else if (formData.username.length < 3) {
      newErrors.username = t('users_username_min_length');
    }

    // Password validation
    if (!editingUser && !formData.password.trim()) {
      // Password is required for new users
      newErrors.password = t('users_password_required_new');
    } else if (formData.password.trim() && formData.password.trim().length < 6) {
      // Password must be at least 6 characters if provided
      newErrors.password = t('users_password_min_length');
    }

    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('users_email_invalid');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      const submitData: any = {
        username: formData.username,
        email: formData.email || null,
        full_name: formData.full_name || null,
        role: formData.role,
      };

      if (editingUser) {
        // For edit, include password only if provided
        const updateData: any = {
          email: submitData.email,
          full_name: submitData.full_name,
          role: submitData.role,
          is_active: formData.is_active,
        };
        if (formData.password.trim()) {
          updateData.password = formData.password;
        }
        await authAPI.updateUser(editingUser.id, updateData);
      } else {
        // Include password for new users
        submitData.password = formData.password;
        await authAPI.createUser(submitData);
      }

      resetForm();
      fetchUsers();
      alert(editingUser ? t('users_updated_success') : t('users_created_success'));
    } catch (error: any) {
      console.error('Error saving user:', error);
      alert(error.response?.data?.detail || t('users_save_failed'));
    }
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      password: '', // Don't pre-fill password
      email: user.email || '',
      full_name: user.full_name || '',
      role: user.role,
      is_active: user.is_active,
    });
    setShowForm(true);
    setErrors({});
  };

  const handleDelete = async (id: number) => {
    if (id === currentUser?.id) {
      alert(t('users_cannot_delete_self'));
      return;
    }

    if (!confirm(t('users_confirm_delete'))) return;

    try {
      await authAPI.deleteUser(id);
      fetchUsers();
      alert(t('users_deleted_success'));
    } catch (error: any) {
      console.error('Error deleting user:', error);
      alert(error.response?.data?.detail || t('users_delete_failed'));
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      password: '',
      email: '',
      full_name: '',
      role: 'cashier',
      is_active: true,
    });
    setEditingUser(null);
    setShowForm(false);
    setErrors({});
  };

  const activeUsers = users.filter(u => u.is_active);
  const displayedUsers = showInactive ? users : activeUsers;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>👥 {t('user_management_title')}</h1>
          <p>{t('users_subtitle')}</p>
        </div>
        <button
          className="button button-primary"
          onClick={() => setShowForm(!showForm)}
        >
          {showForm ? `✖ ${t('cancel')}` : `➕ ${t('users_add_button')}`}
        </button>
      </div>

      {/* Summary Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '20px',
          marginBottom: '30px',
        }}
      >
        <div className="card">
          <h3>{t('users_total_users')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#3498db' }}>
            {users.length}
          </div>
        </div>
        <div className="card">
          <h3>{t('users_active_users')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#2ecc71' }}>
            {activeUsers.length}
          </div>
        </div>
        <div className="card">
          <h3>{t('users_inactive_users')}</h3>
          <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#e74c3c' }}>
            {users.length - activeUsers.length}
          </div>
        </div>
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="card" style={{ marginBottom: '30px' }}>
          <h2>{editingUser ? t('users_edit_form_title') : t('users_add_form_title')}</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="form-group">
                <label>{t('username')} *</label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => {
                    setFormData({ ...formData, username: e.target.value });
                    if (errors.username) {
                      setErrors({ ...errors, username: '' });
                    }
                  }}
                  placeholder={t('enter_username')}
                  disabled={!!editingUser}
                />
                {errors.username && (
                  <span style={{ color: '#e74c3c', fontSize: '12px' }}>{errors.username}</span>
                )}
              </div>

              <div className="form-group">
                <label>{editingUser ? t('users_password_edit_label') : `${t('password')} *`}</label>
                <input
                  type="password"
                  required={!editingUser}
                  value={formData.password}
                  onChange={(e) => {
                    setFormData({ ...formData, password: e.target.value });
                    if (errors.password) {
                      setErrors({ ...errors, password: '' });
                    }
                  }}
                  placeholder={editingUser ? t('users_password_keep_placeholder') : t('enter_password')}
                />
                {errors.password && (
                  <span style={{ color: '#e74c3c', fontSize: '12px' }}>{errors.password}</span>
                )}
              </div>

              <div className="form-group">
                <label>{t('users_full_name')}</label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  placeholder={t('users_full_name_placeholder')}
                />
              </div>

              <div className="form-group">
                <label>{t('users_email')}</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => {
                    setFormData({ ...formData, email: e.target.value });
                    if (errors.email) {
                      setErrors({ ...errors, email: '' });
                    }
                  }}
                  placeholder="email@example.com"
                />
                {errors.email && (
                  <span style={{ color: '#e74c3c', fontSize: '12px' }}>{errors.email}</span>
                )}
              </div>

              <div className="form-group">
                <label>{t('users_role')} *</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  required
                >
                  <option value="cashier">{t('users_role_cashier')}</option>
                  <option value="manager">{t('users_role_manager')}</option>
                  <option value="super_admin">{t('users_role_super_admin')}</option>
                </select>
              </div>

              <div className="form-group">
                <label>{t('status')}</label>
                <select
                  value={formData.is_active ? 'true' : 'false'}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value === 'true' })}
                >
                  <option value="true">{t('users_status_active')}</option>
                  <option value="false">{t('users_status_inactive')}</option>
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
              <button type="submit" className="button button-primary">
                {editingUser ? `💾 ${t('users_update_button')}` : `➕ ${t('users_add_button')}`}
              </button>
              <button type="button" className="button button-secondary" onClick={resetForm}>
                {t('cancel')}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter */}
      <div className="card" style={{ marginBottom: '20px', padding: '15px' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
          />
          <span style={{ fontWeight: 'bold' }}>{t('users_show_inactive')}</span>
        </label>
      </div>

      {/* Users Table */}
      <div className="card">
        <h2>{t('users_table_title')}</h2>
        {loading ? (
          <p>{t('users_loading')}</p>
        ) : displayedUsers.length === 0 ? (
          <p>{t('users_no_records')}</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t('username')}</th>
                <th>{t('users_full_name')}</th>
                <th>{t('users_email')}</th>
                <th>{t('users_role')}</th>
                <th>{t('status')}</th>
                <th>{t('users_last_login')}</th>
                <th>{t('users_created')}</th>
                <th>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {displayedUsers.map((user) => (
                <tr key={user.id} style={{ opacity: user.is_active ? 1 : 0.6 }}>
                  <td style={{ fontWeight: 'bold' }}>
                    {user.id === currentUser?.id && (
                      <span style={{ marginRight: '5px', color: '#3498db' }}>👤</span>
                    )}
                    {user.username}
                  </td>
                  <td>{user.full_name || '-'}</td>
                  <td>{user.email || '-'}</td>
                  <td>
                    <span
                      style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor:
                          user.role === 'super_admin'
                            ? '#fadbd8'
                            : user.role === 'manager'
                              ? '#fce4b6'
                              : '#d5f4e6',
                        color:
                          user.role === 'super_admin'
                            ? '#721c24'
                            : user.role === 'manager'
                              ? '#7d6608'
                              : '#0f5132',
                      }}
                    >
                      {t(`users_role_${user.role}`)}
                    </span>
                  </td>
                  <td>
                    <span
                      style={{
                        padding: '4px 12px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: user.is_active ? '#d5f4e6' : '#fadbd8',
                        color: user.is_active ? '#0f5132' : '#721c24',
                      }}
                    >
                      {user.is_active ? `✓ ${t('users_status_active')}` : `✗ ${t('users_status_inactive')}`}
                    </span>
                  </td>
                  <td>{user.last_login ? new Date(user.last_login).toLocaleString() : '-'}</td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                  <td>
                    
                      <>
                        <button
                          className="button button-sm button-secondary"
                          onClick={() => handleEdit(user)}
                          style={{ marginRight: '5px' }}
                        >
                          ✏️ {t('edit')}
                        </button>
                        <button
                          className="button button-sm button-danger"
                          onClick={() => handleDelete(user.id)}
                        >
                          🗑️ {t('users_delete_btn')}
                        </button>
                      </>
                    {user.id !== currentUser?.id ? (<span></span>) : (
                      <span style={{ color: '#95a5a6', fontSize: '12px' }}>{t('users_current_user')}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

export default Users;
