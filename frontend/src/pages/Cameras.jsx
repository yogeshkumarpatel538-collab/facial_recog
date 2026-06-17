import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Stack,
  FormControlLabel,
  Switch,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import StopIcon from '@mui/icons-material/Stop';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { camerasApi } from '../api/cameras';
import CameraFormDialog from '../components/cameras/CameraFormDialog';
import CameraDetailDrawer from '../components/cameras/CameraDetailDrawer';
import LoadingScreen from '../components/common/LoadingScreen';
import ErrorAlert from '../components/common/ErrorAlert';
import { useAuth } from '../context/AuthContext';
import { getErrorMessage } from '../utils/storage';

export default function Cameras() {
  const { isAdmin } = useAuth();
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCamera, setEditingCamera] = useState(null);
  const [detailCameraId, setDetailCameraId] = useState(null);
  const [activeOnly, setActiveOnly] = useState(false);
  const [actionError, setActionError] = useState('');

  const { data: cameras = [], isLoading, error } = useQuery({
    queryKey: ['cameras', activeOnly],
    queryFn: () => camerasApi.list(activeOnly),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['cameras'] });

  const createMutation = useMutation({
    mutationFn: camerasApi.create,
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      setActionError('');
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }) => camerasApi.update(id, payload),
    onSuccess: () => {
      invalidate();
      setDialogOpen(false);
      setEditingCamera(null);
      setActionError('');
    },
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: camerasApi.delete,
    onSuccess: invalidate,
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const enableMutation = useMutation({
    mutationFn: camerasApi.enable,
    onSuccess: invalidate,
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const disableMutation = useMutation({
    mutationFn: camerasApi.disable,
    onSuccess: invalidate,
    onError: (err) => setActionError(getErrorMessage(err)),
  });

  const handleSubmit = (form) => {
    if (editingCamera) {
      updateMutation.mutate({ id: editingCamera.id, payload: form });
    } else {
      createMutation.mutate(form);
    }
  };

  const openCreate = () => {
    setEditingCamera(null);
    setDialogOpen(true);
  };

  const openEdit = (camera) => {
    setEditingCamera(camera);
    setDialogOpen(true);
  };

  const handleDelete = (camera) => {
    if (window.confirm(`Delete camera "${camera.name}"?`)) {
      deleteMutation.mutate(camera.id);
    }
  };

  const isSaving = createMutation.isPending || updateMutation.isPending;

  if (isLoading) return <LoadingScreen message="Loading cameras..." />;

  return (
    <Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" mb={3} gap={2}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Camera Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure RTSP cameras for people counting
          </Typography>
        </Box>
        <Stack direction="row" alignItems="center" gap={2}>
          <FormControlLabel
            control={
              <Switch checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />
            }
            label="Active only"
          />
          {isAdmin && (
            <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
              Add Camera
            </Button>
          )}
        </Stack>
      </Stack>

      <ErrorAlert error={error ? getErrorMessage(error) : actionError} onClose={() => setActionError('')} />

      <Card>
        <TableContainer sx={{ overflowX: 'auto' }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Location</TableCell>
                <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>RTSP URL</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {cameras.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      {activeOnly ? 'No active cameras' : 'No cameras configured'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                cameras.map((camera) => (
                  <TableRow key={camera.id} hover>
                    <TableCell>
                      <Typography fontWeight={600}>{camera.name}</Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: { md: 'none' } }}>
                        {camera.location}
                      </Typography>
                    </TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                      {camera.location}
                    </TableCell>
                    <TableCell
                      sx={{
                        display: { xs: 'none', lg: 'table-cell' },
                        maxWidth: 280,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {camera.rtsp_url}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={camera.active ? 'Active' : 'Disabled'}
                        color={camera.active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View details">
                        <IconButton size="small" onClick={() => setDetailCameraId(camera.id)}>
                          <InfoOutlinedIcon />
                        </IconButton>
                      </Tooltip>
                      {isAdmin && (
                        <>
                          <Tooltip title={camera.active ? 'Disable' : 'Enable'}>
                            <IconButton
                              size="small"
                              onClick={() =>
                                camera.active
                                  ? disableMutation.mutate(camera.id)
                                  : enableMutation.mutate(camera.id)
                              }
                            >
                              {camera.active ? <StopIcon /> : <PlayArrowIcon />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit">
                            <IconButton size="small" onClick={() => openEdit(camera)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton size="small" color="error" onClick={() => handleDelete(camera)}>
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      <CameraFormDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingCamera(null);
        }}
        onSubmit={handleSubmit}
        camera={editingCamera}
        loading={isSaving}
      />

      <CameraDetailDrawer
        cameraId={detailCameraId}
        open={!!detailCameraId}
        onClose={() => setDetailCameraId(null)}
      />
    </Box>
  );
}
