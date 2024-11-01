import React, { useContext, useEffect, useState } from 'react';
import axios from 'axios';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Stack from '@mui/material/Stack';
import CardHeader from '@mui/material/CardHeader';
import IconButton from '@mui/material/IconButton';


import { Iconify } from 'src/components/iconify';
import { Label } from 'src/components/label';
import { Grid, TextareaAutosize, Tooltip } from '@mui/material';
import { fDateTime } from 'src/utils/format-time';
import { LoadingContext } from 'src/auth/context/loading-context';
import { CONFIG } from 'src/config-global';


// ----------------------------------------------------------------------

export function ItemDetailsItems({ item, senitronItem, setItem, setSenitronItem }) {
  const { setLoading, setError, setComponent } = useContext(LoadingContext);
  const [currentItem, setCurrentItem] = useState(item);
  const [currentSenitronItem, setCurrentSenitronItem] = useState(senitronItem);

  useEffect(() => {
    const socket = new WebSocket(`wss://${CONFIG.apiHost}/${CONFIG.apiDomain}/ws/inventory_items/`);
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'created' || message.type === 'updated') {
        setCurrentItem((prevItem) => {
          if (message.item.itemId === prevItem?.itemId) {
            return message.item;
          }
          return prevItem;
        });
      }
    };
    return () => {
      socket.close();
    };
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`wss://${CONFIG.apiHost}/${CONFIG.apiDomain}/ws/senitron_inventory_items_assets/`);
    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'created' || message.type === 'updated') {
        setCurrentSenitronItem((prevItem) => {
          if (message.item.itemNumber === prevItem?.itemNumber) {
            return message.item;
          }
          return prevItem;
        });
      }
    };
    return () => {
      socket.close();
    };
  }, []);


  const renderTotal = (
    <Stack spacing={1} alignItems="flex-start" sx={{ p: 3, textAlign: 'left', typography: 'body2' }}>
      <Grid container spacing={2}>
        {currentItem.itemId && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>ID: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {currentItem.itemId || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {currentItem.sku && (
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
        {currentItem.rate && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Rate: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> $ {parseFloat(currentItem.rate).toFixed(2) || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        <Grid container item xs={12}>
          <Grid item xs={3}>
            <Box sx={{ color: 'text.secondary' }}>Stock On Hand (Zoho): </Box>
          </Grid>
          <Grid item xs={9}>
            <Box sx={{ typography: 'subtitle2' }}>
              <Label color="default"> {parseInt(currentItem.stockOnHand, 10) || '-'} </Label>
            </Box>
          </Grid>
        </Grid>
        {currentSenitronItem?.senitronItem?.qty && (
          <Grid container item xs={12}>
            <Grid item xs={3}>
              <Box sx={{ color: 'text.secondary' }}>Quantity (Senitron): </Box>
            </Grid>
            <Grid item xs={9}>
              <Box sx={{ typography: 'subtitle2' }}>
                <Label color="default"> {parseInt(currentSenitronItem?.senitronItem?.qty, 10) || '-'} </Label>
              </Box>
            </Grid>
          </Grid>
        )}
        {currentSenitronItem?.text3 && (
          <Grid container item xs={12}>
            <Grid item xs={3}>
              <Box sx={{ color: 'text.secondary' }}>Info (Senitron): </Box>
            </Grid>
            <Grid item xs={9}>
              <Box sx={{ typography: 'subtitle2' }}>
                <Label color="default"> {currentSenitronItem?.text3 || '-'} </Label>
              </Box>
            </Grid>
          </Grid>
        )}
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
        )}
        {/* {currentItem.description && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Description: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2', maxWidth: '100%' }}>
                  <TextareaAutosize
                    aria-label="empty textarea"
                    placeholder="Empty"
                    value={currentItem.description || '-'}
                    disabled
                    minRows={8}
                    maxRows={10}
                    style={{
                      width: isMobile ? '70%' : '100%',
                      resize: 'none',
                      padding: '8px',
                      borderRadius: '4px',
                      borderColor: '#ccc',
                    }}
                  />
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
                setComponent(`inventory item (SKU: ${currentItem.sku}, ID: ${currentItem.itemId}) details`);
                setLoading(true);
                axios
                  .post(`${CONFIG.apiUrl}/api_zoho/load/inventory_items/`)
                  .then(() => {
                    axios
                      .post(`${CONFIG.apiUrl}/api_senitron/load/senitron_inventory_items/`)
                      .then(() => {
                        setItem(currentItem);
                        axios
                          .post(`${CONFIG.apiUrl}/api_senitron/load/senitron_inventory_item_assets/`)
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
                            setLoading(false);
                          });
                      })
                      .catch((err) => {
                        console.error('Error fetching senitron inventory item:', err);
                        setError('There was an error fetching senitron inventory item.');
                      })
                      .finally(() => {
                        setLoading(false);
                      });
                  })
                  .catch((err) => {
                    console.error('Error fetching inventory item:', err);
                    setError('There was an error fetching the inventory item.');
                  })
                  .finally(() => {
                    setLoading(false);
                  });
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
