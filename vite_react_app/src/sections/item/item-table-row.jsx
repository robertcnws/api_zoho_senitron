import React, { useContext } from 'react';

import { LoadingContext } from 'src/auth/context/loading-context';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import MenuList from '@mui/material/MenuList';
import MenuItem from '@mui/material/MenuItem';
import TableRow from '@mui/material/TableRow';
import Checkbox from '@mui/material/Checkbox';
import TableCell from '@mui/material/TableCell';
import IconButton from '@mui/material/IconButton';

import { useBoolean } from 'src/hooks/use-boolean';

import { Label } from 'src/components/label';
import { Iconify } from 'src/components/iconify';
import { ConfirmDialog } from 'src/components/custom-dialog';
import { usePopover, CustomPopover } from 'src/components/custom-popover';

// ----------------------------------------------------------------------

export function ItemTableRow({ row, selected, onEditRow, onSelectRow, onDeleteRow, onViewRow }) {

  const { isMobile } = useContext(LoadingContext);

  const confirm = useBoolean();

  const popover = usePopover();

  const quickEdit = useBoolean();

  return (
    <>
      <TableRow hover selected={selected} aria-checked={selected} tabIndex={-1}>

        <TableCell padding="checkbox">
          <Checkbox id={row.itemId} checked={selected} onClick={onSelectRow} />
        </TableCell>
        {/* <TableCell>
          <Stack spacing={2} direction="row" alignItems="center">
            <Avatar alt={row.name} src={row.avatarUrl} />

            <Stack sx={{ typography: 'body2', flex: '1 1 auto', alignItems: 'flex-start' }}>
              <Link color="inherit" onClick={onEditRow} sx={{ cursor: 'pointer' }}>
                {row.name}
              </Link>
              <Box component="span" sx={{ color: 'text.disabled' }}>
                {row.email}
              </Box>
            </Stack>
          </Stack>
        </TableCell> */}

        <TableCell sx={{ whiteSpace: 'nowrap' }}>{row.sku}</TableCell>

        <TableCell sx={{ whiteSpace: 'nowrap' }}>{row.name}</TableCell>

        <TableCell>
          <Label
            variant="soft"
            color={
              (row.status === 'active' && 'success') ||
              (row.status === 'confirmation_pending' && 'warning') ||
              (row.status === 'inactive' && 'error') ||
              'default'
            }
          >
            {row.status}
          </Label>
        </TableCell>

        <TableCell sx={{ whiteSpace: 'nowrap' }}>{parseInt(row.stockOnHand, 10)}</TableCell>
        <TableCell>
          <Label
            variant="soft"
            color={
              (row.syncedWithSenitron && 'success' || 'error' )
            }
          >
            {row.syncedWithSenitron ? 'Yes' : 'No'}
          </Label>
        </TableCell>

        <TableCell>
          <Stack direction="row" alignItems="center">
            {/* <Tooltip title="Quick Edit" placement="top" arrow>
              <IconButton
                color={quickEdit.value ? 'inherit' : 'default'}
                onClick={quickEdit.onTrue}
              >
                <Iconify icon="solar:pen-bold" />
              </IconButton>
            </Tooltip> */}

            <IconButton color={popover.open ? 'inherit' : 'default'} onClick={popover.onOpen}>
              <Iconify icon="eva:more-vertical-fill" />
            </IconButton>
          </Stack>
        </TableCell>
      </TableRow>

      <CustomPopover
        open={popover.open}
        anchorEl={popover.anchorEl}
        onClose={popover.onClose}
        slotProps={{ arrow: { placement: 'right-top' } }}
      >
        <MenuList>
          <MenuItem
            onClick={() => {
              onViewRow();
              popover.onClose();
            }}
          >
            <Iconify icon="solar:eye-bold" />
            View Item
          </MenuItem>
          <MenuItem
            onClick={() => {
              confirm.onTrue();
              popover.onClose();
            }}
            sx={{ color: 'error.main' }}
          >
            <Iconify icon="solar:trash-bin-trash-bold" />
            Delete Item
          </MenuItem>

        </MenuList>
      </CustomPopover>

      <ConfirmDialog
        open={confirm.value}
        onClose={confirm.onFalse}
        title="Delete"
        content={`Are you sure want to delete item: ${row.sku} (${row.name})?`}
        action={
          <Button variant="contained" color="error" onClick={onDeleteRow}>
            Delete
          </Button>
        }
      />
    </>
  );
}
