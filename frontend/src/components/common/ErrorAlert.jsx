import { Alert, AlertTitle, Collapse } from '@mui/material';

export default function ErrorAlert({ error, title = 'Error', onClose }) {
  if (!error) return null;

  const message = typeof error === 'string' ? error : error?.message || 'Something went wrong';

  return (
    <Collapse in={!!error}>
      <Alert severity="error" onClose={onClose} sx={{ mb: 2 }}>
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Collapse>
  );
}
