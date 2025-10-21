import dayjs from 'dayjs';
import axios from 'axios';
import { useMemo, useEffect, useContext, useCallback } from 'react';

import Stack from '@mui/material/Stack';
import MenuList from '@mui/material/MenuList';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
import IconButton from '@mui/material/IconButton';
import InputAdornment from '@mui/material/InputAdornment';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { formHelperTextClasses } from '@mui/material/FormHelperText';

import { generateItemShipmentPrintablePDF } from 'src/utils/printable-pdf';

import { CONFIG } from 'src/config-global';

import { Iconify } from 'src/components/iconify';
import { usePopover, CustomPopover } from 'src/components/custom-popover';

import { LoadingContext } from 'src/auth/context/loading-context';
import { Box, FormControlLabel, Switch } from '@mui/material';


// ----------------------------------------------------------------------

export function ShipmentTableToolbarListSkuHistory({ filters, onResetPage, dataFiltered, dateError, setUpdating, setTitleLinearProgress }) {
  const popover = usePopover();
  const userLogged = useMemo(() => JSON.parse(localStorage.getItem('userLogged')), []);

  const { setLoading, setError, setComponent } = useContext(LoadingContext);


  useEffect(() => {
    setComponent('sales orders');
  }, [setComponent]);

  useEffect(() => {
    const today = dayjs();
    if (!filters.state.startDate && !filters.state.endDate) {
      filters.setState({
        startDate: today,
        endDate: today,
      });
    }
  }, [filters]);

  const handleFilterName = useCallback(
    (event) => {
      onResetPage();
      filters.setState({ sku: event.target.value });
    },
    [filters, onResetPage]
  );

  const handleFilterDate = useCallback(
    (nameDate, newValue) => {
      setUpdating(true);
      onResetPage();
      const isoString = newValue.toISOString();
      filters.setState({ [nameDate]: dayjs(isoString) });
    },
    [filters, onResetPage, setUpdating]
  );

  return (
    <>
      <Stack
        spacing={2}
        alignItems={{ xs: 'flex-end', md: 'center' }}
        direction={{ xs: 'column', md: 'row' }}
        sx={{ p: 2.5, pr: { xs: 2.5, md: 1 } }}
      >
        {/* <DatePicker
          label="Start date"
          value={filters.state.startDate}
          onChange={handleFilterStartDate}
          slotProps={{ textField: { fullWidth: true } }}
          sx={{ maxWidth: { md: 200 } }}
          format='YYYY-MM-DD'
        /> */}

        <DatePicker
          label="Start Date"
          value={filters.state.startDate}
          onChange={(newValue) => handleFilterDate('startDate', newValue)}
          slotProps={{
            textField: {
              fullWidth: true,
            },
          }}
          sx={{
            maxWidth: { md: 200 },
            [`& .${formHelperTextClasses.root}`]: {
              position: { md: 'absolute' },
              bottom: { md: -40 },
            },
          }}
          format='YYYY-MM-DD'
        />

        <DatePicker
          label="End Date"
          value={filters.state.endDate}
          onChange={(newValue) => handleFilterDate('endDate', newValue)}
          slotProps={{
            textField: {
              fullWidth: true,
              error: dateError,
              helperText: dateError ? 'End date must be later than start date' : null,
            },
          }}
          sx={{
            maxWidth: { md: 200 },
            mr: { md: 10 },
            [`& .${formHelperTextClasses.root}`]: {
              position: { md: 'absolute' },
              bottom: { md: -40 },
            },
          }}
          format='YYYY-MM-DD'
        />

        <Box sx={{ width: 'fit-content' }}>
          <FormControlLabel
            control={
              <Switch
                checked={filters.state.ignoreMull}
                onChange={(event) => {
                  filters.setState({ ignoreMull: event.target.checked });
                  onResetPage();
                }}
              />
            }
            label="Ignore Mull SKUs"
            sx={{ alignSelf: 'flex-start', '& .MuiFormControlLabel-label': { fontSize: 15, width: 150 } }}
          />
        </Box>

        <Stack direction="row" alignItems="center" spacing={2} flexGrow={1} sx={{ width: 1 }}>
          <TextField
            fullWidth
            value={filters.state.sku}
            onChange={handleFilterName}
            placeholder="Search Item SKU, Package NUMBER or Shipment NUMBER..."
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
              generateItemShipmentPrintablePDF({ data: dataFiltered, isHistory: true, filters });
            }}
          >
            <Iconify icon="solar:printer-minimalistic-bold" />
            Print
          </MenuItem>
          <MenuItem
            onClick={() => {
              popover.onClose();
              // setLoading(true);
              setUpdating(true);
              setTitleLinearProgress('Fetching updates shipments from Zoho...');
              axios
                .post(`${CONFIG.apiUrl}/api_zoho/load/inventory_shipments/`, {
                  start_date: filters.state.endDate.format('YYYY-MM-DD'),
                  username: userLogged.data.username,
                })
                .then(() => {
                  console.log('Inventory shipments and packages fetched');
                })
                .catch((err) => {
                  console.error('Error fetching inventory shipments and packages:', err);
                  setError('There was an error fetching the inventory shipments and packages.');
                })
                .finally(() => {
                  // setLoading(false);
                  setUpdating(false);
                });
            }}
          >
            <Iconify icon="mdi:update" />
            Fetch Updates from Zoho
          </MenuItem>
        </MenuList>
      </CustomPopover>
    </>
  );
}
