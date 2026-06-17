import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControlLabel,
  Switch,
  Stack,
} from '@mui/material';

const emptyForm = {
  name: '',
  rtsp_url: '',
  location: '',
  active: true,
};

export default function CameraFormDialog({ open, onClose, onSubmit, camera, loading }) {
  const [form, setForm] = useState(emptyForm);
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (camera) {
      setForm({
        name: camera.name || '',
        rtsp_url: camera.rtsp_url || '',
        location: camera.location || '',
        active: camera.active ?? true,
      });
    } else {
      setForm(emptyForm);
    }
    setErrors({});
  }, [camera, open]);

  const validate = () => {
    const next = {};
    if (!form.name.trim()) next.name = 'Name is required';
    if (!form.rtsp_url.trim()) next.rtsp_url = 'RTSP URL is required';
    else if (!/^rtsps?:\/\/.+/i.test(form.rtsp_url.trim())) {
      next.rtsp_url = 'Must be a valid rtsp:// or rtsps:// URL';
    }
    if (!form.location.trim()) next.location = 'Location is required';
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit(form);
  };

  const update = (field) => (e) => {
    const value = field === 'active' ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>{camera ? 'Edit Camera' : 'Add Camera'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Name"
              value={form.name}
              onChange={update('name')}
              error={!!errors.name}
              helperText={errors.name}
              fullWidth
              required
            />
            <TextField
              label="RTSP URL"
              value={form.rtsp_url}
              onChange={update('rtsp_url')}
              error={!!errors.rtsp_url}
              helperText={errors.rtsp_url || 'e.g. rtsp://192.168.1.10:554/stream1'}
              fullWidth
              required
            />
            <TextField
              label="Location"
              value={form.location}
              onChange={update('location')}
              error={!!errors.location}
              helperText={errors.location}
              fullWidth
              required
            />
            <FormControlLabel
              control={<Switch checked={form.active} onChange={update('active')} />}
              label="Active"
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? 'Saving...' : camera ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
