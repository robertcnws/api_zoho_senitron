import React, { useEffect, useMemo, useState } from 'react';
import { useSetState } from 'src/hooks/use-set-state';
import { fDate } from 'src/utils/format-time';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import CardHeader from '@mui/material/CardHeader';
import ListItemText from '@mui/material/ListItemText';
import { CustomPopover, usePopover } from 'src/components/custom-popover';

import { Iconify } from 'src/components/iconify';
import { Scrollbar } from 'src/components/scrollbar';
import { MenuItem, MenuList, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
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

const TABLE_HEAD = [
  { id: 'sku', label: 'SKU', alignRight: false },
  { id: 'live', label: 'Live', alignRight: false },
  { id: 'removed', label: 'Removed', alignRight: false },
  { id: 'killed', label: 'Killed', alignRight: false },
  { id: '' },
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
  globalDateFilters,
  setStateWidthModal,
  ...other
}) {

  const date = fDate(globalDateFilters.state.endDate, 'YYYY-MM-DD');

  const [modalDataFiltered, setModalDataFiltered] = useState(null);
  const modalItemSerialsDetailsTitle = 'Item Serials Details';
  const modalListItemsSerialsTitle = 'List Items Serials';
  const [isItemTable, setIsItemTable] = useState(false);
  const popover = usePopover();

  const STATUS_OPTIONS = [
    
  ]

  const filtersItemTable = useSetState({
    name: '',
    status: STATUS_OPTIONS.includes(localStorage.getItem('itemStatus')) ? localStorage.getItem('itemStatus') : 'all',
});

  useEffect(() => {
    setStateWidthModal('md');
    setIsItemTable(false);
  }, [setStateWidthModal]);

  return (
    <>
      <Card {...other}>
        <CardHeader
          title={title}
          subheader={subheader}
          action={
            <>
              {isItemTable && (
                <IconButton onClick={popover.onOpen}>
                  <Iconify icon="eva:more-vertical-fill" />
                </IconButton>
              )}
              <Button
                size="small"
                color="inherit"
                endIcon={<Iconify icon="eva:arrow-ios-forward-fill" width={18} sx={{ ml: -0.5 }} />}
                onClick={() => {
                  setIsItemTable(!isItemTable);
                  setStateWidthModal(!isItemTable ? 'lg' : 'md');
                }}
              >
                View {isItemTable ? 'in List' : 'in Table'}
              </Button>

            </>
          }
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
              {!isItemTable ? list.map((item, index) => (
                <Item
                  key={`${item.itemId}-${index}`}
                  item={item}
                  setModalDataFiltered={setModalDataFiltered}
                  handleOpenModal={handleOpenModal}
                  date={date}
                />
              )) : (
                <>

                  {/* <Card sx={{ minHeight: isMobile ? '100%' : '70vh' }}>
                    {list?.length > 0 && (
                      <Tabs
                        value={filters.state.status}
                        onChange={handleFilterStatus}
                        sx={{
                          bgcolor: 'whitesmoke',
                          px: 2.5,
                          boxShadow: (theme) =>
                            `inset 0 -2px 0 0 ${varAlpha(theme.vars.palette.grey['500Channel'], 0.08)}`,
                        }}
                      >
                        {STATUS_OPTIONS.map((tab) => (
                          <Tab
                            key={tab.value}
                            iconPosition="end"
                            value={tab.value}
                            label={tab.label}
                            sx={{
                              bgcolor: tab.value === 'lost' && tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length > 0 ? 'error.main' :
                                tab.value === 'not_matched' && tableData.filter((it) => it.differenceShipped > 0 && !it.isReconciled && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length > 0 ? 'warning.main' : 'transparent',
                              color: tab.value === 'lost' && tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length > 0 ? 'white' : 'inherit',
                              px: 1.5,
                              py: 1,
                              borderRadius: '8px',
                            }}
                            icon={
                              <Label
                                variant={
                                  ((tab.value === 'lost' || tab.value === 'not_matched' || tab.value === filters.state.status) && 'filled') ||
                                  'soft'
                                }
                                color={
                                  (tab.value === 'matched' && 'success') ||
                                  (tab.value === 'not_matched' && 'warning') ||
                                  (tab.value === 'lost' && 'error') ||
                                  'default'
                                }
                              >
                                {tab.value === 'matched' ?
                                  tableData.filter((it) => it.differenceShipped === 0 && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length :
                                  tab.value === 'not_matched' ?
                                    tableData.filter((it) => it.differenceShipped > 0 && !it.isReconciled && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length :
                                    tab.value === 'lost' ?
                                      tableData.filter((it) => it.differenceShipped < 0 && !it.isReconciled && it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length :
                                      tableData.filter((it) => it.date === fDate(filters.state.endDate, 'YYYY-MM-DD')).length
                                }
                              </Label>
                            }
                          />
                        ))}
                      </Tabs>
                    )}

                    <ItemTableShippedLogsToolbar
                      filters={filters}
                      onResetPage={table.onResetPage}
                      options={{ values: STATUS_OPTIONS.map((option) => option.label) }}
                      dataFiltered={dataFiltered}
                      headersCSV={headersCSV}
                      setUpdating={setUpdating}
                      setTitleLinearProgress={setTitleLinearProgress}
                      isListAll={false}
                      globalDateFilters={globalDateFilters}
                      title={filters.state.status === 'all' ? 'All SKUs' :
                        filters.state.status === 'lost' ? 'Losts Shipped SKUs' :
                          filters.state.status === 'matched' ? 'Shipped SKUs matched' :
                            filters.state.status === 'not_matched' ? 'Shipped SKUs NOT matched' :
                              filters.state.status
                      }
                    />

                    {canReset && (
                      <ItemTableFiltersResult
                        filters={filters}
                        totalResults={dataFiltered.length}
                        onResetPage={table.onResetPage}
                        hasNotAll={false}
                        sx={{ p: 2.5, pt: 0 }}
                      />
                    )}

                    <Box sx={{ position: 'relative' }}>

                      <Scrollbar>
                        {tableData?.length > 0 ? (
                          <TableContainer sx={{
                            maxHeight: filters.state.status === 'all' ? 405 : 305,
                            minHeight: filters.state.status === 'all' ? 405 : 305
                          }}>
                            <Table size={table.dense ? 'small' : 'medium'} sx={{ minWidth: 960 }} stickyHeader>
                              <TableHeadCustom
                                order={table.order}
                                orderBy={table.orderBy}
                                headLabel={TABLE_HEAD}
                                rowCount={dataFiltered.length}
                                numSelected={table.selected.length}
                                onSort={table.onSort}
                              />
                              <TableBody>
                                {dataFiltered
                                  .slice(
                                    table.page * table.rowsPerPage,
                                    table.page * table.rowsPerPage + table.rowsPerPage
                                  )
                                  .map((row) => (
                                    <React.Fragment key={row.itemId}>
                                      <TableRow key={row.itemId} sx={{ cursor: 'pointer' }}>
                                        <TableCell>
                                          <Link color="inherit" onClick={() => handleViewRow(row.itemId)} underline="always" sx={{ cursor: 'pointer' }}>
                                            {row.sku}
                                          </Link>
                                        </TableCell>
                                        <TableCell>
                                          <ListItemText
                                            primary={fDate(row.date)}
                                            primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                                          />
                                        </TableCell>
                                        <TableCell>{row.itemTotalQty}</TableCell>
                                        <TableCell>
                                          {!row.isReconciled ? row.shippedSerialsQuantity : row.itemTotalQty}
                                        </TableCell>
                                        <TableCell>
                                          <Label
                                            sx={{ cursor: 'pointer' }}
                                            variant="soft"
                                            color={
                                              (row.differenceShipped === 0 ? 'success' :
                                                row.differenceShipped > 0 && !row.isReconciled ? 'warning' :
                                                  row.differenceShipped < 0 && !row.isReconciled ? 'error' : 'info')
                                            }
                                          >
                                            {!row.isReconciled ? row.differenceShipped : 0}
                                          </Label>
                                        </TableCell>
                                        <TableCell align="right" sx={{ px: 1, whiteSpace: 'nowrap' }}>
                                          {row.linePackages?.length > 0 ? (
                                            <IconButton
                                              color={openRowIds.has(row.itemId) ? 'inherit' : 'default'}
                                              onClick={() => toggleRow(row.itemId)}
                                              sx={{ ...(openRowIds.has(row.itemId) && { bgcolor: 'action.hover' }) }}
                                            >
                                              <Iconify icon={openRowIds.has(row.itemId) ? "eva:arrow-ios-upward-fill" : "eva:arrow-ios-downward-fill"} />
                                            </IconButton>
                                          ) : (
                                            <Label
                                              variant="soft"
                                              color="warning"
                                            >
                                              No Data
                                            </Label>
                                          )}
                                        </TableCell>
                                      </TableRow>
                                      {openRowIds.has(row.itemId) && renderSecondary(row)}
                                    </React.Fragment>
                                  ))}

                                <TableEmptyRows
                                  height={table.dense ? 56 : 56 + 20}
                                  emptyRows={emptyRows(table.page, table.rowsPerPage, dataFiltered.length)}
                                />

                                <TableNoData notFound={notFound} />
                              </TableBody>
                            </Table>
                          </TableContainer>
                        ) : (
                          <TableContainer sx={{ width: '100%', bgcolor: 'background.paper', p: 1 }}>
                            <Table>
                              <TableBody>
                                <TableNoData notFound={tableData.length === 0} />
                              </TableBody>
                            </Table>
                          </TableContainer>
                        )}
                      </Scrollbar>
                    </Box>

                    <TablePaginationCustom
                      page={table.page}
                      dense={table.dense}
                      count={dataFiltered.length}
                      rowsPerPage={table.rowsPerPage}
                      onPageChange={(event, newPage) => {
                        localStorage.setItem('itemPage', newPage);
                        table.onChangePage(event, newPage);
                      }}
                      onChangeDense={table.onChangeDense}
                      onRowsPerPageChange={(event) => {
                        localStorage.setItem('itemRowsPerPage', event.target.value);
                        table.onChangeRowsPerPage(event);
                      }}
                    />
                  </Card> */}

                  <TableContainer sx={{ height: 350 }}>
                    <Table stickyHeader>
                      <TableHead>
                        {TABLE_HEAD.map((head) => (
                          <TableCell key={head.id} align={head.alignRight ? 'right' : 'left'}>
                            {head.label}
                          </TableCell>
                        ))}
                      </TableHead>
                      <TableBody>
                        {list.map((item, index) => (
                          <ItemInTable
                            key={`${item.itemId}-${index}`}
                            item={item}
                            setModalDataFiltered={setModalDataFiltered}
                            handleOpenModal={handleOpenModal}
                            date={date}
                          />
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
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
            }}
          >
            <Iconify icon="solar:printer-minimalistic-bold" />
            Print
          </MenuItem>
        </MenuList>
      </CustomPopover>

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

function ItemInTable({ item, sx, setModalDataFiltered, handleOpenModal, date, ...other }) {
  return (
    <>
      {item.logs.length > 0 && (
        <TableRow sx={{ display: 'flex', alignItems: 'center', ...sx }} {...other}>
          <TableCell>{item.sku}</TableCell>
        </TableRow>
      )
      }
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
                      if (h.currentStatusName?.toLowerCase().includes('live')
                        && !acc.seen.has(h.serialNumber)
                        && fDate(h.createdTime, 'YYYY-MM-DD').includes(date)) {
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
                  }</b> Shipped <span style={{ color: 'orange', fontSize: 'smaller' }}> </span>
                  <span style={{ color: 'orange', fontSize: 'smaller' }}>
                    (Removed: <b>{
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
