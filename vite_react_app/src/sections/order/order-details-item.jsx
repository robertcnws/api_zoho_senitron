import React, { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Stack from '@mui/material/Stack';
import CardHeader from '@mui/material/CardHeader';
import IconButton from '@mui/material/IconButton';
import { Grid } from '@mui/material';
import { Label } from 'src/components/label';

import { Iconify } from 'src/components/iconify';
import { line } from 'stylis';

// ----------------------------------------------------------------------

export function OrderDetailsItems({ order }) {

  const [lineItems, setLineItems] = useState([]);

  useEffect(() => {
    const items = order.lineItems;
    console.log('items', items);
    // setLineItems(items instanceof Array ? items : JSON.parse(items));
  }, [order.lineItems]);

  const renderItems = lineItems.map((item) => (
    <Stack key={item.item_id} direction="row" alignItems="center" justifyContent="space-between">
      <Stack direction="row" alignItems="center" spacing={2}>
        <Box component="img" sx={{ width: 48, height: 48, borderRadius: 1.5 }} />
        <Stack spacing={1}>
          <Label color="info">{item.name}</Label>
          <Label color="text.secondary">{item.sku}</Label>
        </Stack>
      </Stack>
    </Stack>
  ));

  const renderTotal = (
    <Stack spacing={2} alignItems="flex-start" sx={{ p: 3, textAlign: 'left', typography: 'body2' }}>
      <Grid container spacing={2}>
        {order.salesorderId && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>ID: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {order.salesorderId || '-'} </Label>
                </Box>
              </Grid>

            </Grid>
          </>
        )}
        {order.customerName && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Customer: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {order.customerName || '-'} </Label>
                </Box>
              </Grid>

            </Grid>
          </>
        )}
        {order.totalQuantity && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Total Quantity: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {order.totalQuantity || '-'} </Label>
                </Box>
              </Grid>

            </Grid>
          </>
        )}
        {order.total && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Totals: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box sx={{ color: 'text.secondary' }}>Subtotal: </Box>
                    </Grid>
                    <Grid item xs={1}>
                      <Box alignItems="flex-end" sx={{ p: 0, textAlign: 'right', typography: 'body2' }}>
                        <Label color="default"> {parseFloat(order.subTotal).toFixed(2) || '-'} </Label>
                      </Box>
                    </Grid>
                  </Grid>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box sx={{ color: 'text.secondary' }}>Tax Total: </Box>
                    </Grid>
                    <Grid item xs={1}>
                      <Box alignItems="flex-end" sx={{ p: 0, textAlign: 'right', typography: 'body2' }}>
                        <Label color="default"> {parseFloat(order.taxTotal).toFixed(2) || '-'} </Label>
                      </Box>
                    </Grid>
                  </Grid>
                  <Grid container spacing={2}>
                    <Grid item xs={4}>
                      <Box sx={{ color: 'text.secondary' }}>Total: </Box>
                    </Grid>
                    <Grid item xs={1}>
                      <Box alignItems="flex-end" sx={{ p: 0, textAlign: 'right', typography: 'body2' }}>
                        <Label color="default"> {parseFloat(order.total).toFixed(2) || '-'} </Label>
                      </Box>
                    </Grid>
                  </Grid>
                </Box>
              </Grid>

            </Grid>
          </>
        )}
        {order.lineItems && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Items (Products): </Box>
              </Grid>
              <Grid item xs={9}>
                {renderItems}
              </Grid>

            </Grid>
          </>
        )}
      </Grid>
    </Stack>
  );

  return (
    <Card>
      <CardHeader
        title="Details"
        action={
          <IconButton>
            <Iconify icon="solar:pen-bold" />
          </IconButton>
        }
      />

      {renderTotal}
    </Card>
  );
}
