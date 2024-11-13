import { Box, Button, TextField, Stack, TableContainer, Table, TableHead, TableRow, TableCell, TableBody, InputAdornment } from "@mui/material";
import { usePopover, CustomPopover } from 'src/components/custom-popover';
import IconButton from '@mui/material/IconButton';
import MenuList from '@mui/material/MenuList';
import MenuItem from '@mui/material/MenuItem';
import { Iconify } from 'src/components/iconify';
import { ConfirmDialog } from 'src/components/custom-dialog';
import { Label } from "src/components/label";
import { alpha, useTheme } from '@mui/material/styles';
import { generatePrintablePDF } from 'src/utils/printable-pdf';
import ExportCSV from "src/utils/export-csv";

export function ModalSublistItems({ 
  openModal, 
  setOpenModal, 
  modalDataFiltered, 
  modalTitle, 
  headersCSV,
  modalButtonColor, 
  filters, 
  handleFilterName, 
  handleViewRow, 
  ...other 
}) {

  const theme = useTheme();
  const popover = usePopover();


  return (
    <>
      <ConfirmDialog
        open={openModal}
        onClose={() => setOpenModal(false)}
        title={`${modalTitle} (${modalDataFiltered?.length} items)`}
        maxWidth='lg'
        content={
          <Box sx={{ width: '100%', bgcolor: 'background.paper', p: 1 }}>
            <Stack direction="row" alignItems="center" spacing={1} flexGrow={1} sx={{ width: 1 }}>
              <TextField
                fullWidth
                value={filters.state.name}
                onChange={handleFilterName}
                placeholder="Search by item (NAME, SKU, or ID)..."
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Iconify icon="eva:search-fill" sx={{ color: 'text.disabled' }} />
                    </InputAdornment>
                  ),
                }}
              />
              {/* <Button
                style={{ height: '50px' }}
                color="inherit"
                variant="outlined"
                startIcon={<Iconify icon="solar:printer-minimalistic-bold" />}
                onClick={() => { generatePrintablePDF({ data: modalDataFiltered, title: modalTitle }) }}
              >
                Print
              </Button> */}
              <IconButton onClick={popover.onOpen}>
                <Iconify icon="eva:more-vertical-fill" />
              </IconButton>
            </Stack>
            <TableContainer sx={{ maxHeight: 440 }}>
              <Table size='small' stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>No.</TableCell>
                    <TableCell sx={{ width: 300 }}>SKU</TableCell>
                    <TableCell sx={{ width: 500 }}>Name</TableCell>
                    <TableCell sx={{ width: 200 }}>On Hand</TableCell>
                    <TableCell sx={{ width: 200 }}>RFID Count</TableCell>
                    <TableCell sx={{ width: 200 }}>Difference</TableCell>
                    <TableCell sx={{ width: 200 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {modalDataFiltered?.map((item, index) => (
                    <TableRow key={`${item.itemId}-${index}`}>
                      <TableCell sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        {index + 1}
                      </TableCell>
                      <TableCell colSpan={!item.sku ? 2 : 0} sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        {item.sku || (item.itemNumber ? `Item ID: ${item.itemNumber}` : `Item Name: ${item.name}`)}
                      </TableCell>
                      {item.sku &&
                        <TableCell>{item.name}</TableCell>
                      }
                      <TableCell sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        <Label color='default'>
                          {item.stockOnHand}
                        </Label>
                      </TableCell>
                      <TableCell sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        <Label color='default'>
                          {item.quantity}
                        </Label>
                      </TableCell>
                      <TableCell sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        <Label color={item.difference === 0 ? 'success' : item.difference > 0 ? 'warning' : 'error'}>
                          {item.difference}
                        </Label>
                      </TableCell>
                      <TableCell sx={{ bgcolor: !item.sku ? alpha(theme.palette.error.main, 0.1) : 'none' }}>
                        <Button
                          onClick={() => {
                            handleViewRow(item.itemId);
                          }}
                          sx={{ color: modalButtonColor }}
                        >
                          <Iconify icon="solar:eye-bold" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        }
      />
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
              generatePrintablePDF({ data: modalDataFiltered, title: modalTitle });
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
            <ExportCSV data={modalDataFiltered} headers={headersCSV} buttonText="Export CSV" docName={modalTitle} />
          </MenuItem>
          
        </MenuList>
      </CustomPopover>
    </>
  );
}