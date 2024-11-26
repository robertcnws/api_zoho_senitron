import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Avatar from '@mui/material/Avatar';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import CardHeader from '@mui/material/CardHeader';
import ListItemText from '@mui/material/ListItemText';

import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';

// ----------------------------------------------------------------------

export function BankingContacts({ title, subheader, list, ...other }) {
  return (
    <Card {...other}>
      <CardHeader
        title={title}
        subheader={subheader}
        action={
          <Button
            size="small"
            color="inherit"
            endIcon={<Iconify icon="eva:arrow-ios-forward-fill" width={18} sx={{ ml: -0.5 }} />}
          >
            View all
          </Button>
        }
      />

      <Scrollbar sx={{ maxHeight: 394 }}>
        <Box
          sx={{
            p: 3,
            gap: 3,
            display: 'flex',
            flexDirection: 'column',
            minWidth: 360,
          }}
        >
          {list.map((item) => (
            <Item key={item.itemId} item={item} />
          ))}
        </Box>
      </Scrollbar>
    </Card>
  );
}

function Item({ item, sx, ...other }) {
  return (
    <Box key={item.id} sx={{ gap: 2, display: 'flex', alignItems: 'center', ...sx }} {...other}>
      <ListItemText primary={item.sku}
        secondary={
          <>
            {item.differences.news.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', typography: 'body2', color: 'success.main' }}>
                <Iconify icon="eva:arrow-ios-upward-fill" width={16} height={16} />
                <span>{item.differences.news.length} New(s)</span>
              </Box>
            )}
            {item.differences.losts.length > 0 && (
              <Box sx={{ display: 'flex', alignItems: 'center', typography: 'body2', color: 'error.main' }}>
                <Iconify icon="eva:arrow-ios-downward-fill" width={16} height={16} />
                <span>{item.differences.losts.length} Lost(s)</span>
              </Box>
            )}
          </>
        } />

      <Tooltip title="See details">
        <IconButton>
          <Iconify icon="solar:transfer-horizontal-bold-duotone" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
