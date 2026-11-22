import { useEffect, useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { useAuthStore } from '../../store/authStore';
import axiosClient from '../../api/axiosClient';

const roles = { viewer: 'Chỉ xem', operator: 'Vận hành', admin: 'Quản trị' };
const message = (err) => typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Không thực hiện được. Kiểm tra thông tin và kết nối.';

export default function AccountPanel() {
  const user = useAuthStore((s) => s.user);
  const restore = useAuthStore((s) => s.restore);
  const login = useAuthStore((s) => s.login);
  const logout = useAuthStore((s) => s.logout);
  const [open, setOpen] = useState(false), [manage, setManage] = useState(false);
  const [email, setEmail] = useState(''), [password, setPassword] = useState('');
  const [error, setError] = useState(''), [busy, setBusy] = useState(false);
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'operator' });
  useEffect(() => { restore(); }, [restore]);
  const signIn = async (event) => {
    event.preventDefault(); setBusy(true); setError('');
    try { await login(email, password); setPassword(''); setOpen(false); }
    catch (err) { setError(message(err)); }
    finally { setBusy(false); }
  };
  const loadUsers = async () => {
    setError('');
    try { setUsers(await axiosClient.get('/auth/users')); setManage(true); }
    catch (err) { setError(message(err)); }
  };
  const create = async () => {
    setBusy(true); setError('');
    try { await axiosClient.post('/auth/users', form); setForm({ name: '', email: '', password: '', role: 'operator' }); await loadUsers(); }
    catch (err) { setError(message(err)); }
    finally { setBusy(false); }
  };
  const toggle = async (row) => {
    try { await axiosClient.patch(`/auth/users/${row.id}/access`, { active: !row.active }); await loadUsers(); }
    catch (err) { setError(message(err)); }
  };
  return <Box sx={{ mb: 2, p: 2, bgcolor: '#F1F5F9', borderRadius: 2 }}>
    {user ? <Stack spacing={1}><Typography variant="body2">{user.name} · {roles[user.role]}</Typography>
      <Stack direction="row"><Button onClick={async () => { try { await logout(); } catch (err) { setError(message(err)); } }}>Đăng xuất</Button>
        {user.role === 'admin' && <Button onClick={loadUsers}>Tài khoản</Button>}</Stack></Stack>
      : <><Typography variant="body2">Bạn đang xem dữ liệu. Đăng nhập để nhập bài, xác minh hoặc tìm đường.</Typography>
        <Button onClick={() => { setError(''); setOpen(true); }}>Đăng nhập</Button></>}
    {error && !open && !manage && <Alert severity="error">{error}</Alert>}
    <Dialog open={open} onClose={busy ? undefined : () => setOpen(false)} fullWidth maxWidth="xs">
      <Box component="form" onSubmit={signIn}><DialogTitle>Đăng nhập vận hành</DialogTitle><DialogContent><Stack spacing={2} mt={1}>
        <TextField autoFocus required label="Email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
        <TextField required label="Mật khẩu" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        {error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Đóng</Button>
        <Button type="submit" variant="contained" disabled={busy}>{busy ? 'Đang đăng nhập…' : 'Đăng nhập'}</Button></DialogActions></Box>
    </Dialog>
    <Dialog open={manage} onClose={() => setManage(false)} fullWidth maxWidth="sm"><DialogTitle>Quản lý tài khoản</DialogTitle>
      <DialogContent><Stack spacing={2}>
        {users.map((row) => <Stack key={row.id} direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="body2">{row.name} · {row.email} · {roles[row.role]}{!row.active ? ' · Đã khóa' : ''}</Typography>
          <Button disabled={row.id === user?.id} onClick={() => toggle(row)}>{row.active ? 'Khóa' : 'Mở khóa'}</Button></Stack>)}
        <Typography fontWeight={700}>Tạo tài khoản</Typography>
        {['name', 'email', 'password'].map((key) => <TextField key={key} label={{ name: 'Tên', email: 'Email', password: 'Mật khẩu (ít nhất 12 ký tự)' }[key]}
          type={key === 'password' ? 'password' : 'text'} value={form[key]} onChange={(e) => setForm((old) => ({ ...old, [key]: e.target.value }))} />)}
        <TextField select label="Quyền" value={form.role} onChange={(e) => setForm((old) => ({ ...old, role: e.target.value }))}>
          {Object.entries(roles).map(([key, label]) => <MenuItem key={key} value={key}>{label}</MenuItem>)}
        </TextField>{error && <Alert severity="error">{error}</Alert>}
      </Stack></DialogContent><DialogActions><Button onClick={() => setManage(false)}>Đóng</Button>
        <Button disabled={busy || !form.email || !form.name || form.password.length < 12} onClick={create}>Tạo tài khoản</Button></DialogActions>
    </Dialog>
  </Box>;
}
