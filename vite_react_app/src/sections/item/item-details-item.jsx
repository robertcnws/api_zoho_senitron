import React, { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Stack from '@mui/material/Stack';
import CardHeader from '@mui/material/CardHeader';
import IconButton from '@mui/material/IconButton';

import { fDateTime } from 'src/utils/format-time';


import { Iconify } from 'src/components/iconify';
import { Label } from 'src/components/label';
import { Grid, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextareaAutosize, Tooltip } from '@mui/material';
import { LoadingContext } from 'src/auth/context/loading-context';
import { CONFIG } from 'src/config-global';


// ----------------------------------------------------------------------

export function ItemDetailsItems({ item, senitronItem, setItem, setSenitronItem, setUpdating }) {
  const { setLoading, setError, setComponent } = useContext(LoadingContext);
  const [currentItem, setCurrentItem] = useState(null);
  const [currentSenitronItem, setCurrentSenitronItem] = useState(null);


  useEffect(() => {
    if (item)
      setCurrentItem(item);
    if (senitronItem)
      setCurrentSenitronItem(senitronItem);
  }, [item, senitronItem]);


  // useEffect(() => {
  //   const socket = new WebSocket(`wss://${CONFIG.apiHost}/${CONFIG.apiDomain}/ws/senitron_inventory_items_assets/`);
  //   socket.onmessage = (event) => {
  //     const message = JSON.parse(event.data);
  //     if (message.type === 'created' || message.type === 'updated') {
  //       setCurrentSenitronItem((prevItem) => {
  //         if (message.item.itemNumber === prevItem?.itemNumber) {
  //           return message.item;
  //         }
  //         return prevItem;
  //       });
  //     }
  //   };
  //   return () => {
  //     socket.close();
  //   };
  // }, []);


  const renderTotal = (
    <Stack spacing={1} alignItems="flex-start" sx={{ p: 3, textAlign: 'left', typography: 'body2' }}>
      <Grid container spacing={2}>
        {currentItem?.itemId && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>ID: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {currentItem?.itemId || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {currentItem?.sku && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>SKU: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default">{currentItem.sku || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {currentItem?.rate && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Rate: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> $ {parseFloat(currentItem.rate).toFixed(2) || '0.00'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        <Grid container item xs={12}>
          <Grid item xs={3}>
            <Box sx={{ color: 'text.secondary' }}>On Hand: </Box>
          </Grid>
          <Grid item xs={9}>
            <Box sx={{ typography: 'subtitle2' }}>
              <Label color="default"> {parseInt(currentItem?.stockOnHand, 10) || '0'} </Label>
            </Box>
          </Grid>
        </Grid>
        {currentSenitronItem?.count && (
          <Grid container item xs={12}>
            <Grid item xs={3}>
              <Box sx={{ color: 'text.secondary' }}>RFID Count: </Box>
            </Grid>
            <Grid item xs={9}>
              <Box sx={{ typography: 'subtitle2' }}>
                <Label color="default"> {parseInt(currentSenitronItem?.count, 10) || '0'} </Label>
              </Box>
            </Grid>
          </Grid>
        )}
        {currentItem?.stockOnHand && currentSenitronItem?.count && (
          <Grid container item xs={12}>
            <Grid item xs={3}>
              <Box sx={{ color: 'text.secondary' }}>Difference: </Box>
            </Grid>
            <Grid item xs={9}>
              <Box sx={{ typography: 'subtitle2' }}>
                <Label color={
                  (parseInt(currentSenitronItem?.count, 10) - parseInt(currentItem?.stockOnHand, 10) === 0 ? 'success' :
                    (parseInt(currentSenitronItem?.count, 10) - parseInt(currentItem?.stockOnHand, 10) > 0 ? 'warning' : 'error'))
                }>
                  {(parseInt(currentSenitronItem?.count, 10) - parseInt(currentItem?.stockOnHand, 10)) || '0'}
                </Label>
              </Box>
            </Grid>
          </Grid>
        )}
        {currentSenitronItem?.assets && (
          <Grid container item xs={12}>
            <Grid item xs={3}>
              <Box sx={{ color: 'text.secondary' }}>Info Assets: </Box>
            </Grid>
            <Grid item xs={9}>
              <TableContainer sx={{ height: '400px' }}>
                <Table stickyHeader>
                  <TableHead>
                    <TableRow sx={{ p: 0 }}>
                      <TableCell>Antenna</TableCell>
                      <TableCell>Serial</TableCell>
                      <TableCell>Last Zone</TableCell>
                      <TableCell>Info</TableCell>
                      <TableCell>Last Seen</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {currentSenitronItem?.assets.filter((asset) => asset.lastSeenAntenna && asset.lastZone && asset.text3)
                      .map((asset, index) => (
                        <TableRow key={`${asset.id}-${index}-${asset.serialNumber}`}>
                          <TableCell>
                            {asset.lastSeenAntenna}
                          </TableCell>
                          <TableCell>
                            {asset.serialNumber}
                          </TableCell>
                          <TableCell>
                            {asset.lastZone}
                          </TableCell>
                          <TableCell>
                            {asset.text3}
                          </TableCell>
                          <TableCell>
                            {asset.lastSeen ? fDateTime(asset.lastSeen) : `Updated:  ${fDateTime(asset.updatedAt)}`}
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        )}
        {/*
        {currentSenitronItem?.handheldReader && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Hand Held Reader (Senitron): </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {currentSenitronItem?.handheldReader || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )} */}

      </Grid>
    </Stack>
  );

  return (
    <Card>
      <CardHeader
        title="Item Details"
        action={
          <Tooltip
            title="Update from APIs"
            arrow
            sx={{
              '& .MuiTooltip-tooltip': {
                backgroundColor: '#000000',
                color: 'white',
                fontSize: '0.875rem',
              },
            }}
          >
            <IconButton
              onClick={() => {
                const payload = {
                  item_number: currentItem?.itemId,
                };
                // setComponent(`inventory item (SKU: ${currentItem?.sku}, ID: ${currentItem?.itemId}) details`);
                // setLoading(true);
                setUpdating(true);  
                axios
                  .post(`${CONFIG.apiUrl}/api_zoho/load/inventory_items/`, payload)
                  .then(() => {
                    axios
                      .post(`${CONFIG.apiUrl}/api_senitron/load/senitron_inventory_item_assets/`, payload)
                      .then(() => {
                        setSenitronItem(currentSenitronItem);
                        console.log('Zoho Inventory item fetched');
                        console.log('Senitron Inventory item fetched');
                      })
                      .catch((err) => {
                        console.error('Error fetching senitron inventory item asset:', err);
                        setError('There was an error fetching senitron inventory item asset.');
                      })
                      .finally(() => {
                        // setLoading(false);
                        setUpdating(false);
                      });
                  })
                  .catch((err) => {
                    console.error('Error fetching inventory item:', err);
                    setError('There was an error fetching the inventory item.');
                  })
              }}
            >
              <Iconify icon="mdi:update" />
            </IconButton>
          </Tooltip>
        }
      />
      {renderTotal}
    </Card>
  );
}
