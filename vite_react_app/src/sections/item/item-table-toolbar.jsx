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
import { Checkbox, FormControl, InputLabel, OutlinedInput, Select } from '@mui/material';
import { generatePrintablePDF } from 'src/utils/printable-pdf';
import ExportCSV from 'src/utils/export-csv';

// ----------------------------------------------------------------------

export function ItemTableToolbar({ filters, onResetPage, options, dataFiltered, headersCSV, setUpdating, title }) {
  const popover = usePopover();

  const { setLoading, setError, setComponent } = useContext(LoadingContext);

  const handleFilterName = useCallback(
    (event) => {
      onResetPage();
      filters.setState({ name: event.target.value });
    },
    [filters, onResetPage]
  );

  const handleFilterSynced = useCallback(
    (event) => {
      const newValue =
        typeof event.target.value === 'string' ? event.target.value.split(',') : event.target.value;

      onResetPage();
      filters.setState({ syncedWithSenitron: newValue });
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
        {/* <FormControl sx={{ flexShrink: 0, width: { xs: 1, md: 200 } }}>
          <InputLabel htmlFor="item-filter-syncedWithSenitron-select-label">Synced With Senitron</InputLabel>

          <Select
            multiple
            value={filters.state.syncedWithSenitron}
            onChange={handleFilterSynced}
            input={<OutlinedInput label="Synced With Senitron" />}
            renderValue={(selected) => selected.map((value) => value).join(', ')}
            inputProps={{ id: 'item-filter-syncedWithSenitron-select-label' }}
            sx={{ textTransform: 'capitalize' }}
          >
            {options.values.map((option) => (
              <MenuItem key={option} value={option}>
                <Checkbox
                  disableRipple
                  size="small"
                  checked={filters.state.syncedWithSenitron.includes(option)}
                />
                {option}
              </MenuItem>
            ))}
          </Select>
        </FormControl> */}

        <Stack direction="row" alignItems="center" spacing={2} flexGrow={1} sx={{ width: 1 }}>
          <TextField
            fullWidth
            value={filters.state.name}
            onChange={handleFilterName}
            placeholder="Search by item (NAME, SKU, ID or STOCK ON HAND)..."
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
              generatePrintablePDF({ data: dataFiltered, title });
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
            {/* <Iconify icon="solar:export-bold" />
            Export CSV */}
            <ExportCSV data={dataFiltered} headers={headersCSV} buttonText="Export CSV" docName={title} />
          </MenuItem>
          <MenuItem
            onClick={() => {
              popover.onClose();
              // setLoading(true);
              // setComponent('zoho inventory items');
              setUpdating(true);
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
                  setUpdating(false);
                });
            }}
          >
            <Iconify icon="mdi:update" />
            Fetch Updates from Zoho
          </MenuItem>
          <MenuItem
            onClick={() => {
              popover.onClose();
              // setLoading(true);
              // setComponent('senitron items');
              setUpdating(true);
              axios
                .post(`${CONFIG.apiUrl}/api_senitron/load/senitron_inventory_item_assets/`)
                .then(() => {
                  console.log('Zoho Inventory items fetched');
                  console.log('Senitron Inventory items fetched');
                })
                .catch((err) => {
                  console.error('Error fetching senitron inventory items assets:', err);
                  setError('There was an error fetching senitron inventory items assets.');
                })
                .finally(() => {
                  // setLoading(false);
                  setUpdating(false);
                });
            }}
          >
            <Iconify icon="mdi:sync" />
            Sync with Senitron
          </MenuItem>
        </MenuList>
      </CustomPopover>
    </>
  );
}
