import { Box, Button, TextField, Stack, TableContainer, Table, TableHead, TableRow, TableCell, TableBody, InputAdornment } from "@mui/material";
import { Iconify } from 'src/components/iconify';
import { ConfirmDialog } from 'src/components/custom-dialog';

export function ModalSublistItems({ openModal, setOpenModal, modalDataFiltered, modalTitle, modalButtonColor, filters, handleFilterName, handleViewRow, ...other }) {
  return (
    <ConfirmDialog
        open={openModal}
        onClose={() => setOpenModal(false)}
        title={modalTitle}
        maxWidth='lg'
        content={
          <Box sx={{ width: '100%', bgcolor: 'background.paper', p: 2 }}>
            <Stack direction="row" alignItems="center" spacing={2} flexGrow={1} sx={{ width: 1 }}>
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
            </Stack>
            <TableContainer sx={{ maxHeight: 440 }}>
              <Table size='small' stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell>No.</TableCell>
                    <TableCell sx={{ width: 300 }}>SKU</TableCell>
                    <TableCell sx={{ width: 500 }}>Name</TableCell>
                    <TableCell sx={{ width: 200 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {modalDataFiltered?.map((item, index) => (
                    <TableRow key={item.itemId}>
                      <TableCell>{index + 1}</TableCell>
                      <TableCell>{item.sku}</TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>
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
  );
}