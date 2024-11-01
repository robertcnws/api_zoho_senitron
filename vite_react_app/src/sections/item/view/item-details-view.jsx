import { useState, useCallback } from 'react';

import Stack from '@mui/material/Stack';
import Grid from '@mui/material/Unstable_Grid2';

import { paths } from 'src/routes/paths';

import { DashboardContent } from 'src/layouts/dashboard';

import { ItemDetailsInfo } from '../item-details-info';
import { ItemDetailsItems } from '../item-details-item';
import { ItemDetailsToolbar } from '../item-details-toolbar';
import { ItemDetailsSenitronItems } from '../item-details-senitron-item';

// ----------------------------------------------------------------------

export function ItemDetailsView({ item, senitronItem, setItem, setSenitronItem }) {
  const [status, setStatus] = useState(item?.status);

  const handleChangeStatus = useCallback((newValue) => {
    setStatus(newValue);
  }, []);

  return (
    <DashboardContent>
      <ItemDetailsToolbar
        item={item}
        backLink={localStorage.getItem('routeByOrder') ? paths.dashboard.order.root : 
          (localStorage.getItem('routeByAnalytics') ? paths.dashboard.general.analytics : paths.dashboard.item.root)}
        status={status}
      />

      <Grid container spacing={3}>
        <Grid xs={12} md={8}>
          <Stack spacing={3} direction={{ xs: 'column-reverse', md: 'column' }}>
            <ItemDetailsItems item={item} senitronItem={senitronItem} setItem={setItem} setSenitronItem={setSenitronItem}/>
            {/* <ItemDetailsSenitronItems item={senitronItem} /> */}

            {/* <ItemDetailsHistory history={item?.history} /> */}
          </Stack>
        </Grid>

        <Grid xs={12} md={4}>
          <ItemDetailsInfo item={item} senitronItem={senitronItem} setItem={setItem} setSenitronItem={setSenitronItem}/>
        </Grid>
      </Grid>
    </DashboardContent>
  );
}
