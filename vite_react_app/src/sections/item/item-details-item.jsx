import React, { useContext } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Stack from '@mui/material/Stack';
import Avatar from '@mui/material/Avatar';
import CardHeader from '@mui/material/CardHeader';
import IconButton from '@mui/material/IconButton';
import ListItemText from '@mui/material/ListItemText';

import { fCurrency } from 'src/utils/format-number';

import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { Label } from 'src/components/label';
import { Grid, TextareaAutosize } from '@mui/material';
import { fDateTime } from 'src/utils/format-time';
import { LoadingContext } from 'src/auth/context/loading-context';


// ----------------------------------------------------------------------

export function ItemDetailsItems({ item }) {

  const { isMobile } = useContext(LoadingContext);

  const renderTotal = (
    <Stack spacing={1} alignItems="flex-start" sx={{ p: 3, textAlign: 'left', typography: 'body2' }}>
      <Grid container spacing={2}>
        {item.itemId && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>ID: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {item.itemId || '-'} </Label>
                </Box>
              </Grid>

            </Grid>
          </>
        )}
        {/* {item.name && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Name: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {item.name || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )} */}
        {item.sku && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>SKU: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default">{item.sku || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        <Grid container item xs={12}>
          <Grid item xs={3}>
            <Box sx={{ color: 'text.secondary' }}>Stock On Hand: </Box>
          </Grid>
          <Grid item xs={9}>
            <Box sx={{ typography: 'subtitle2' }}>
              <Label color="default"> {parseInt(item.stockOnHand, 10) || '-'} </Label>
            </Box>
          </Grid>
        </Grid>
        {item.source && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Source: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {item.source || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {item.itemType && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Item Type: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {item.itemType || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {item.rate && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Rate: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> $ {parseFloat(item.rate).toFixed(2) || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {/* {item.createdTime && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Created Time: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {fDateTime(item.createdTime) || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )} */}
        {item.lastModifiedTime && (
          <>
            <Grid container item xs={12}>
              <Grid item xs={3}>
                <Box sx={{ color: 'text.secondary' }}>Last Modified Time: </Box>
              </Grid>
              <Grid item xs={9}>
                <Box sx={{ typography: 'subtitle2' }}>
                  <Label color="default"> {fDateTime(item.lastModifiedTime) || '-'} </Label>
                </Box>
              </Grid>
            </Grid>
          </>
        )}
        {item.description && (
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
                    value={item.description || '-'}
                    disabled
                    minRows={8} // Número fijo de filas
                    maxRows={8} // Mismo valor que minRows para evitar el ajuste
                    style={{
                      width: isMobile ? '70%' : '100%',    // Ancho fijo
                      resize: 'none',    // Deshabilita la capacidad de redimensionar manualmente
                      padding: '8px',    // Opcional: Ajusta el padding según tus necesidades
                      borderRadius: '4px', // Opcional: Bordes redondeados
                      borderColor: '#ccc', // Opcional: Color del borde
                    }}
                  />
                </Box>
              </Grid>
            </Grid>
          </>
        )}
      </Grid>

    </Stack >
  );

  return (
    <Card>
      <CardHeader
        title="Details from Zoho"
        action={
          <IconButton>
            <Iconify icon="solar:details" />
          </IconButton>
        }
      />
      {renderTotal}
    </Card>
  );
}
