import React, { useMemo, useState } from 'react';
import { fDate } from 'src/utils/format-time';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import CardHeader from '@mui/material/CardHeader';
import ListItemText from '@mui/material/ListItemText';

import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { Table, TableBody, TableContainer } from '@mui/material';
import { TableNoData } from 'src/components/table';
import { ModalItemSerialsDetails } from './view/modal-item-serials-details';
import { ModalSublistItemsSerials } from './view/modal-sublist-items-serials';


// ----------------------------------------------------------------------

const headersCSV = [
  { label: 'SKU', key: 'sku' },
  { label: 'Date', key: 'createdTime' },
  { label: 'New Serials', key: 'news' },
  { label: 'Lost Serials', key: 'losts' },
];

export function BankingContacts({
  title,
  subheader,
  list,
  openModal,
  setOpenModal,
  handleOpenModal,
  table,
  filters,
  handleFilterName,
  ...other
}) {

  const date = fDate(new Date(), 'YYYY-MM-DD');

  const [modalDataFiltered, setModalDataFiltered] = useState(null);
  const modalItemSerialsDetailsTitle = 'Item Serials Details';
  const modalListItemsSerialsTitle = 'List Items Serials';

  return (
    <>
      <Card {...other}>
        <CardHeader
          title={title}
          subheader={subheader}
        // action={
        //   <Button
        //     size="small"
        //     color="inherit"
        //     endIcon={<Iconify icon="eva:arrow-ios-forward-fill" width={18} sx={{ ml: -0.5 }} />}
        //     onClick={() => {
        //       handleOpenModal('subListItemsSerials');
        //     }}
        //   >
        //     View all
        //   </Button>
        // }
        />

        <Scrollbar sx={{ maxHeight: 394, minHeight: 394 }}>
          {list?.length > 0 ? (
            <Box
              sx={{
                p: 3,
                gap: 3,
                display: 'flex',
                flexDirection: 'column',
                minWidth: 360,
              }}
            >
              {list.map((item, index) => (
                <Item
                  key={`${item.itemId}-${index}`}
                  item={item}
                  setModalDataFiltered={setModalDataFiltered}
                  handleOpenModal={handleOpenModal}
                  date={date}
                />
              ))}
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableBody>
                  <TableNoData notFound={list?.length === 0} />
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Scrollbar>
      </Card>

      <ModalItemSerialsDetails
        openModal={openModal}
        setOpenModal={setOpenModal}
        modalDataFiltered={modalDataFiltered}
        modalTitle={modalItemSerialsDetailsTitle}
        headersCSV={headersCSV}
        table={table}
        date={date}
      />

      <ModalSublistItemsSerials
        openModal={openModal}
        setOpenModal={setOpenModal}
        modalDataFiltered={list}
        headersCSV={headersCSV}
        table={table}
        filters={filters}
        handleFilterName={handleFilterName}
        modalTitle={modalListItemsSerialsTitle}
      />
    </>
  );
}

function Item({ item, sx, setModalDataFiltered, handleOpenModal, date, ...other }) {
  return (
    <Box sx={{ gap: 2, display: 'flex', alignItems: 'center', ...sx }} {...other}>
      <ListItemText
        primary={item.sku}
        secondary={
          <>
            {item.logs.length > 0 && (
              <Box
                component="span"
                sx={{ display: 'inline-flex', alignItems: 'center', typography: 'body2', color: 'success.main', gap: 1 }}
              >
                <Iconify icon="eva:arrow-ios-upward-fill" width={16} height={16} />
                <span>
                  <b>{
                    item.logs.reduce((acc, h) => {
                      if (h.currentStatusName?.toLowerCase().includes('live') && !acc.seen.has(h.serialNumber)) {
                        acc.seen.add(h.serialNumber);
                        acc.count += 1;
                      }
                      return acc;
                    }, { count: 0, seen: new Set() }).count
                  }</b> Live
                </span>
              </Box>
            )}
            {item.logs.length > 0 && (
              <Box
                component="span"
                sx={{ display: 'inline-flex', alignItems: 'center', typography: 'body2', color: 'error.main', gap: 1 }}
              >
                <Iconify icon="eva:arrow-ios-downward-fill" width={16} height={16} />
                <span>
                  <b>{
                    item.logs.reduce((acc, h) => {
                      if (!h.currentStatusName?.toLowerCase().includes('live') && !acc.seen.has(h.serialNumber)) {
                        acc.seen.add(h.serialNumber);
                        acc.count += 1;
                      }
                      return acc;
                    }, { count: 0, seen: new Set() }).count
                  }</b> Shipped <span style={{ color: 'orange', fontSize: 'smaller' }}>------</span> <span>(Removed: <b>{
                    item.logs.reduce((acc, h) => {
                      if (h.currentStatusName?.toLowerCase().includes('remove') && !acc.seen.has(h.serialNumber)) {
                        acc.seen.add(h.serialNumber);
                        acc.count += 1;
                      }
                      return acc;
                    }, { count: 0, seen: new Set() }).count
                  }</b>, Kill: <b>{
                      item.logs.reduce((acc, h) => {
                        if (h.currentStatusName?.toLowerCase().includes('kill') && !acc.seen.has(h.serialNumber)) {
                          acc.seen.add(h.serialNumber);
                          acc.count += 1;
                        }
                        return acc;
                      }, { count: 0, seen: new Set() }).count
                    }</b>)</span>
                </span>
              </Box>
            )}
          </>
        }
      />

      <Tooltip title="See details">
        <IconButton onClick={() => {
          setModalDataFiltered(item);
          handleOpenModal('itemSerialsDetails');
        }}>
          <Iconify icon="solar:transfer-horizontal-bold-duotone" />
        </IconButton>
      </Tooltip>
    </Box>
  );
}
