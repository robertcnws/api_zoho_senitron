import React, { useEffect } from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import Timeline from '@mui/lab/Timeline';
import TimelineDot from '@mui/lab/TimelineDot';
import Typography from '@mui/material/Typography';
import CardHeader from '@mui/material/CardHeader';
import TimelineContent from '@mui/lab/TimelineContent';
import TimelineSeparator from '@mui/lab/TimelineSeparator';
import TimelineConnector from '@mui/lab/TimelineConnector';
import TimelineItem, { timelineItemClasses } from '@mui/lab/TimelineItem';

import { fDateTime } from 'src/utils/format-time';

// ----------------------------------------------------------------------

export function AnalyticsOrderTimeline({ title, subheader, list, onViewDetails, ...other }) {

  const [timelineItems, setTimelineItems] = React.useState(null);

  useEffect(() => {
    const newItems = [];
    list?.forEach((item) => {
      const newItem = {
        id: item.itemNumber,
        title: item.text,
        time: item.text.includes('stock on hand') ? item.dateActualStockOnHand :
          item.text.includes('status') ? item.dateActualStatusZoho :
            item.text.includes('quantity') ? item.dateActualQuantity :
              item.text.includes('created') && item.text.includes('Senitron') ? item.dateActualQuantity :
                item.text.includes('created') && item.text.includes('Zoho') ? item.dateActualStockOnHand : item.dateActualStatusSenitron,
        type: item.text.includes('created') ? 'order1' : item.text.includes('changed') ? 'order4' : item.text.includes('updated') ? 'order3' : 'order2',
      };
      newItems.push(newItem);
    });
    setTimelineItems(newItems);
  }, [list]);

  return (
    <Card {...other}>
      <CardHeader title={title} subheader={subheader} />
      <Box sx={{ maxHeight: 390, overflowY: 'auto' }}>
        <Timeline
          sx={{
            m: 0,
            p: 3,
            [`& .${timelineItemClasses.root}:before`]: {
              flex: 0,
              padding: 0,
            },
          }}
        >
          {timelineItems?.map((item, index) => (
            <Item key={`${item.id}-${index}`} item={item} lastItem={index === list.length - 1} onViewDetails={onViewDetails} />
          ))}
        </Timeline>
      </Box>
    </Card>
  );
}


function Item({ item, lastItem, onViewDetails, ...other }) {
  return (
    <TimelineItem {...other} sx={{ cursor: 'pointer' }} onClick={() => onViewDetails(item.id)}>
      <TimelineSeparator>
        <TimelineDot
          color={
            (item.type === 'order1' && 'primary') ||
            (item.type === 'order2' && 'success') ||
            (item.type === 'order3' && 'info') ||
            (item.type === 'order4' && 'warning') ||
            'error'
          }
        />
        {lastItem ? null : <TimelineConnector />}
      </TimelineSeparator>

      <TimelineContent>
        <Typography variant="subtitle2">{item.title}</Typography>

        <Typography variant="caption" sx={{ color: 'text.disabled' }}>
          {fDateTime(item.time)}
        </Typography>
      </TimelineContent>
    </TimelineItem>
  );
}
