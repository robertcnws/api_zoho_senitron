import { useCallback, useContext, useEffect } from 'react';

import Stack from '@mui/material/Stack';
import MenuList from '@mui/material/MenuList';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';

import { Iconify } from 'src/components/iconify';
import { usePopover, CustomPopover } from 'src/components/custom-popover';
import { CONFIG } from 'src/config-global';
import axios from 'axios';
import { LoadingContext } from 'src/auth/context/loading-context';

// ----------------------------------------------------------------------

export function ItemTableToolbar({ filters, onResetPage }) {
  const popover = usePopover();

  const { setLoading, setError, setComponent } = useContext(LoadingContext);

  useEffect(() => {
    setComponent('items');
  }, [setComponent]);

  const handleFilterName = useCallback(
    (event) => {
      onResetPage();
      filters.setState({ name: event.target.value });
    },
    [filters, onResetPage]
  );


  return (
    <>
      <Stack
        spacing={2}
        alignItems={{ xs: 'flex-end', md: 'center' }}
        direction={{ xs: 'column', md: 'row' }}
        sx={{ p: 2.5, pr: { xs: 2.5, md: 1 } }}
      >

        <Stack direction="row" alignItems="center" spacing={2} flexGrow={1} sx={{ width: 1 }}>
          <TextField
            fullWidth
            value={filters.state.name}
            onChange={handleFilterName}
            placeholder="Search by item name..."
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Iconify icon="eva:search-fill" sx={{ color: 'text.disabled' }} />
                </InputAdornment>
              ),
            }}
          />

          <IconButton onClick={popover.onOpen}>
            <Iconify icon="eva:more-vertical-fill" />
          </IconButton>
        </Stack>
      </Stack>

      <CustomPopover
        open={popover.open}
        anchorEl={popover.anchorEl}
        onClose={popover.onClose}
        slotProps={{ arrow: { placement: 'right-top' } }}
      >
        <MenuList>
          <MenuItem
            onClick={() => {
              popover.onClose();
            }}
          >
            <Iconify icon="solar:printer-minimalistic-bold" />
            Print
          </MenuItem>

          <MenuItem
            onClick={() => {
              popover.onClose();
            }}
          >
            <Iconify icon="solar:import-bold" />
            Import
          </MenuItem>

          <MenuItem
            onClick={() => {
              popover.onClose();
            }}
          >
            <Iconify icon="solar:export-bold" />
            Export
          </MenuItem>
          <MenuItem
            onClick={() => {
              popover.onClose();
              setLoading(true);
              axios
                .post(`${CONFIG.apiUrl}/api_zoho/load/inventory_items/`)
                .then(() => {
                  console.log('Inventory items fetched');
                })
                .catch((err) => {
                  console.error('Error fetching inventory items:', err);
                  setError('There was an error fetching the inventory items.');
                })
                .finally(() => {
                  setLoading(false);
                });
            }}
          >
            <Iconify icon="mdi:sync" />
            Fetch Updates
          </MenuItem>
        </MenuList>
      </CustomPopover>
    </>
  );
}