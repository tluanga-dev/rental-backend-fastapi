# Rental Status Feature - Frontend Integration Guide

**Document Version**: 2.0  
**Date**: 18/01/25  
**Target Audience**: Frontend Developers  
**Backend Version**: Rental Status Feature without direct API endpoints

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [System Settings Configuration](#system-settings-configuration)
3. [Status Display Guidelines](#status-display-guidelines)
4. [Transaction Return Flow Integration](#transaction-return-flow-integration)
5. [Status Types & Business Rules](#status-types--business-rules)
6. [UI Component Examples](#ui-component-examples)
7. [Error Handling](#error-handling)
8. [Testing Strategies](#testing-strategies)

---

## Overview

The Rental Status Feature automatically tracks and updates rental transaction statuses based on business rules. Status calculation happens automatically during:
- **Rental return transactions** - When items are returned
- **Scheduled midnight checks** - Daily automated status updates for overdue items

Frontend applications should focus on:
- Displaying current status from transaction data
- Configuring system settings for scheduled checks
- Handling return transactions that trigger status updates

### Important Notes:
- ⚠️ **No direct status API endpoints** - Status is managed internally
- ✅ **Status available in transaction responses** - Use existing transaction endpoints
- ⚙️ **Configurable via system settings** - Control scheduling and behavior

---

## System Settings Configuration

The rental status feature behavior can be configured through the System Settings API. Frontend applications should provide UI for administrators to manage these settings.

### Base System Settings Endpoint
```
GET/PUT /api/system/settings
```

### Rental Status Related Settings

#### 1. Enable/Disable Automated Status Checks
```typescript
interface RentalStatusCheckEnabled {
  setting_key: "rental_status_check_enabled";
  setting_name: "Rental Status Check Enabled";
  setting_type: "BOOLEAN";
  setting_value: "true" | "false";
  setting_category: "SYSTEM";
  description: "Enable automated rental status checking";
  is_system: true;
}
```

**UI Example:**
```tsx
// React component for toggle
<FormField>
  <Label>Automated Rental Status Checks</Label>
  <Switch
    checked={settings.rental_status_check_enabled === "true"}
    onCheckedChange={(checked) => 
      updateSetting("rental_status_check_enabled", checked ? "true" : "false")
    }
  />
  <HelperText>
    When enabled, system will automatically check and update rental statuses daily
  </HelperText>
</FormField>
```

#### 2. Configure Status Check Time
```typescript
interface RentalStatusCheckTime {
  setting_key: "rental_status_check_time";
  setting_name: "Rental Status Check Time";
  setting_type: "STRING";
  setting_value: "00:00"; // HH:MM format
  setting_category: "SYSTEM";
  description: "Time to run daily rental status check (HH:MM format)";
  is_system: true;
}
```

**UI Example:**
```tsx
// Time picker component
<FormField>
  <Label>Daily Status Check Time</Label>
  <TimePicker
    value={settings.rental_status_check_time}
    onChange={(time) => updateSetting("rental_status_check_time", time)}
    format="HH:mm"
    disabled={settings.rental_status_check_enabled !== "true"}
  />
  <HelperText>
    Time when the system will check for overdue rentals (24-hour format)
  </HelperText>
</FormField>
```

#### 3. Status Log Retention Period
```typescript
interface RentalStatusLogRetention {
  setting_key: "rental_status_log_retention_days";
  setting_name: "Rental Status Log Retention Days";
  setting_type: "INTEGER";
  setting_value: "365";
  setting_category: "SYSTEM";
  description: "Number of days to retain rental status change logs";
  is_system: true;
}
```

**UI Example:**
```tsx
// Number input for retention days
<FormField>
  <Label>Status History Retention</Label>
  <NumberInput
    value={parseInt(settings.rental_status_log_retention_days)}
    onChange={(days) => updateSetting("rental_status_log_retention_days", days.toString())}
    min={30}
    max={3650}
    step={1}
  />
  <HelperText>
    How long to keep rental status change history (minimum 30 days)
  </HelperText>
</FormField>
```

#### 4. Task Scheduler Timezone
```typescript
interface TaskSchedulerTimezone {
  setting_key: "task_scheduler_timezone";
  setting_name: "Task Scheduler Timezone";
  setting_type: "STRING";
  setting_value: "UTC";
  setting_category: "SYSTEM";
  description: "Timezone for scheduled tasks";
  is_system: true;
}
```

**UI Example:**
```tsx
// Timezone selector
<FormField>
  <Label>Scheduler Timezone</Label>
  <Select
    value={settings.task_scheduler_timezone}
    onValueChange={(tz) => updateSetting("task_scheduler_timezone", tz)}
  >
    <SelectContent>
      <SelectItem value="UTC">UTC</SelectItem>
      <SelectItem value="America/New_York">Eastern Time</SelectItem>
      <SelectItem value="America/Chicago">Central Time</SelectItem>
      <SelectItem value="America/Denver">Mountain Time</SelectItem>
      <SelectItem value="America/Los_Angeles">Pacific Time</SelectItem>
      <SelectItem value="Europe/London">London</SelectItem>
      <SelectItem value="Asia/Tokyo">Tokyo</SelectItem>
      {/* Add more timezones as needed */}
    </SelectContent>
  </Select>
  <HelperText>
    Timezone for scheduling automated tasks
  </HelperText>
</FormField>
```

### Complete Settings Update Example

```typescript
// TypeScript service for updating system settings
class SystemSettingsService {
  async updateRentalStatusSettings(settings: {
    enabled: boolean;
    checkTime: string;
    retentionDays: number;
    timezone: string;
  }) {
    const updates = [
      {
        setting_key: "rental_status_check_enabled",
        setting_value: settings.enabled ? "true" : "false"
      },
      {
        setting_key: "rental_status_check_time",
        setting_value: settings.checkTime
      },
      {
        setting_key: "rental_status_log_retention_days",
        setting_value: settings.retentionDays.toString()
      },
      {
        setting_key: "task_scheduler_timezone",
        setting_value: settings.timezone
      }
    ];

    // Update each setting
    for (const update of updates) {
      await this.updateSetting(update.setting_key, update.setting_value);
    }
  }

  private async updateSetting(key: string, value: string) {
    const response = await fetch(`/api/system/settings/${key}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getAuthToken()}`
      },
      body: JSON.stringify({ setting_value: value })
    });

    if (!response.ok) {
      throw new Error(`Failed to update setting ${key}`);
    }
  }
}
```

---

## Status Display Guidelines

Since status is calculated internally and returned with transaction data, frontend applications should:

### 1. Fetch Status from Transaction Endpoints

```typescript
// Get transaction with current status
const transaction = await fetch(`/api/transactions/${transactionId}`);
const data = await transaction.json();

// Access status from response
const headerStatus = data.current_rental_status;
const lineStatuses = data.transaction_lines.map(line => ({
  lineId: line.id,
  status: line.current_rental_status,
  sku: line.sku,
  description: line.description
}));
```

### 2. Status Badge Component

```tsx
interface StatusBadgeProps {
  status: RentalStatus;
  size?: 'sm' | 'md' | 'lg';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const config = {
    ACTIVE: { color: 'green', icon: CheckCircle, label: 'Active' },
    LATE: { color: 'red', icon: AlertCircle, label: 'Late' },
    EXTENDED: { color: 'blue', icon: Clock, label: 'Extended' },
    PARTIAL_RETURN: { color: 'orange', icon: Package, label: 'Partial Return' },
    LATE_PARTIAL_RETURN: { color: 'red', icon: AlertTriangle, label: 'Late Partial' },
    COMPLETED: { color: 'gray', icon: CheckSquare, label: 'Completed' }
  };

  const { color, icon: Icon, label } = config[status] || config.ACTIVE;

  return (
    <Badge variant={color} size={size}>
      <Icon className="w-4 h-4 mr-1" />
      {label}
    </Badge>
  );
};
```

### 3. Transaction List with Status

```tsx
const RentalTransactionList = () => {
  const { data: transactions, isLoading } = useQuery({
    queryKey: ['rental-transactions'],
    queryFn: () => fetchRentalTransactions({ type: 'RENTAL' })
  });

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Transaction #</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Rental Period</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {transactions?.map((tx) => (
          <TableRow key={tx.id}>
            <TableCell>{tx.transaction_number}</TableCell>
            <TableCell>{tx.customer_name}</TableCell>
            <TableCell>
              {formatDate(tx.rental_start_date)} - {formatDate(tx.rental_end_date)}
            </TableCell>
            <TableCell>
              <StatusBadge status={tx.current_rental_status} />
            </TableCell>
            <TableCell>
              <Button
                size="sm"
                onClick={() => navigateToReturn(tx.id)}
                disabled={tx.current_rental_status === 'COMPLETED'}
              >
                Process Return
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
};
```

---

## Transaction Return Flow Integration

When processing returns, the backend automatically calculates and updates status. Frontend should:

### 1. Return Processing Form

```tsx
interface ReturnFormData {
  transaction_id: string;
  return_date: string;
  items_to_return: Array<{
    transaction_line_id: string;
    quantity: number;
    condition?: string;
    notes?: string;
  }>;
  payment_collected?: number;
  refund_issued?: number;
  notes?: string;
}

const ProcessReturn = ({ transactionId }: { transactionId: string }) => {
  const [formData, setFormData] = useState<ReturnFormData>({
    transaction_id: transactionId,
    return_date: new Date().toISOString().split('T')[0],
    items_to_return: []
  });

  const handleSubmit = async () => {
    try {
      // Create return event
      const returnEvent = await createReturnEvent(formData);
      
      // Process inspections if needed
      if (hasInspections) {
        await processInspections(returnEvent.id, inspections);
      }
      
      // Complete return - this triggers status update internally
      const result = await completeReturn(returnEvent.id, {
        payment_collected: formData.payment_collected,
        refund_issued: formData.refund_issued,
        notes: formData.notes
      });
      
      // Refresh transaction to get updated status
      await queryClient.invalidateQueries(['transaction', transactionId]);
      
      toast.success('Return processed successfully. Status updated automatically.');
    } catch (error) {
      toast.error('Failed to process return');
    }
  };

  return (
    <Form onSubmit={handleSubmit}>
      {/* Form fields for return processing */}
    </Form>
  );
};
```

### 2. Post-Return Status Display

```tsx
const ReturnConfirmation = ({ transactionId }: { transactionId: string }) => {
  const { data: transaction } = useQuery({
    queryKey: ['transaction', transactionId],
    queryFn: () => fetchTransaction(transactionId),
    refetchInterval: 5000 // Poll for status updates
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Return Processed Successfully</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <Label>Transaction Status Updated</Label>
            <div className="flex items-center gap-2 mt-1">
              <StatusBadge status={transaction?.current_rental_status} size="lg" />
              <span className="text-sm text-muted-foreground">
                Status automatically calculated based on return
              </span>
            </div>
          </div>
          
          <div>
            <Label>Line Item Status</Label>
            <div className="space-y-2 mt-1">
              {transaction?.transaction_lines.map((line) => (
                <div key={line.id} className="flex items-center justify-between">
                  <span>{line.description}</span>
                  <StatusBadge status={line.current_rental_status} size="sm" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

---

## Status Types & Business Rules

### Header Status Rules

| Status | Condition |
|--------|-----------|
| `ACTIVE` | All items within return timeframe, no returns made |
| `LATE` | At least one item is past the return period |
| `EXTENDED` | Rental period has been extended |
| `PARTIAL_RETURN` | Some items returned, all within timeframe |
| `LATE_PARTIAL_RETURN` | Some items returned AND at least one item is late |
| `COMPLETED` | All items have been returned |

### Line Item Status Rules

| Status | Condition |
|--------|-----------|
| `ACTIVE` | Item within return timeframe, not returned |
| `LATE` | Item past return period, not returned |
| `PARTIAL_RETURN` | Some quantity returned, within timeframe |
| `LATE_PARTIAL_RETURN` | Some quantity returned, past return period |
| `RETURNED` | Full quantity returned |

### Status Priority Order
When multiple conditions apply, the system uses this priority:
1. `COMPLETED` (if all returned)
2. `LATE_PARTIAL_RETURN` (if any late + partial)
3. `LATE` (if any late)
4. `PARTIAL_RETURN` (if any partial)
5. `EXTENDED` (if extended)
6. `ACTIVE` (default)

---

## UI Component Examples

### 1. Admin Settings Panel

```tsx
const RentalStatusSettings = () => {
  const { data: settings, isLoading } = useSystemSettings();
  const updateSetting = useUpdateSystemSetting();

  if (isLoading) return <Spinner />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Rental Status Configuration</CardTitle>
        <CardDescription>
          Configure automated rental status checking behavior
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Automated Checks</Label>
              <p className="text-sm text-muted-foreground">
                Automatically update overdue rental statuses daily
              </p>
            </div>
            <Switch
              checked={settings.rental_status_check_enabled === "true"}
              onCheckedChange={(checked) => 
                updateSetting.mutate({
                  key: "rental_status_check_enabled",
                  value: checked ? "true" : "false"
                })
              }
            />
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>Check Time</Label>
            <div className="flex gap-2">
              <Input
                type="time"
                value={settings.rental_status_check_time}
                onChange={(e) => 
                  updateSetting.mutate({
                    key: "rental_status_check_time",
                    value: e.target.value
                  })
                }
                disabled={settings.rental_status_check_enabled !== "true"}
              />
              <Select
                value={settings.task_scheduler_timezone}
                onValueChange={(value) =>
                  updateSetting.mutate({
                    key: "task_scheduler_timezone",
                    value
                  })
                }
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {timezones.map(tz => (
                    <SelectItem key={tz.value} value={tz.value}>
                      {tz.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <p className="text-sm text-muted-foreground">
              Daily time to check for overdue rentals
            </p>
          </div>

          <Separator />

          <div className="space-y-2">
            <Label>History Retention</Label>
            <div className="flex gap-2 items-center">
              <Input
                type="number"
                value={settings.rental_status_log_retention_days}
                onChange={(e) =>
                  updateSetting.mutate({
                    key: "rental_status_log_retention_days",
                    value: e.target.value
                  })
                }
                min={30}
                max={3650}
                className="w-[120px]"
              />
              <span className="text-sm text-muted-foreground">days</span>
            </div>
            <p className="text-sm text-muted-foreground">
              How long to keep status change history
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

### 2. Status History Viewer (Read from Transaction Events)

```tsx
const StatusHistory = ({ transactionId }: { transactionId: string }) => {
  const { data: events } = useQuery({
    queryKey: ['transaction-events', transactionId],
    queryFn: () => fetchTransactionEvents(transactionId)
  });

  const statusEvents = events?.filter(e => 
    e.event_type === 'STATUS_CHANGE' || 
    e.event_type === 'RETURN_PROCESSED'
  ) || [];

  return (
    <Timeline>
      {statusEvents.map((event, index) => (
        <TimelineItem key={event.id}>
          <TimelinePoint>
            <TimelineIcon>
              {event.event_type === 'RETURN_PROCESSED' ? 
                <Package className="w-4 h-4" /> : 
                <Activity className="w-4 h-4" />
              }
            </TimelineIcon>
          </TimelinePoint>
          <TimelineContent>
            <TimelineTitle>
              {event.event_type === 'RETURN_PROCESSED' ? 
                'Return Processed' : 
                'Status Changed'
              }
            </TimelineTitle>
            <TimelineDescription>
              {event.metadata?.old_status && (
                <span>
                  <StatusBadge status={event.metadata.old_status} size="sm" />
                  {' → '}
                  <StatusBadge status={event.metadata.new_status} size="sm" />
                </span>
              )}
              <div className="text-xs text-muted-foreground mt-1">
                {formatDateTime(event.created_at)}
                {event.created_by && ` by ${event.created_by_name}`}
              </div>
            </TimelineDescription>
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );
};
```

---

## Error Handling

### Settings Update Errors

```typescript
const handleSettingUpdate = async (key: string, value: string) => {
  try {
    await updateSystemSetting(key, value);
    toast.success('Setting updated successfully');
  } catch (error) {
    if (error.response?.status === 403) {
      toast.error('You do not have permission to modify system settings');
    } else if (error.response?.status === 400) {
      toast.error(`Invalid value for ${key}: ${error.response.data.detail}`);
    } else {
      toast.error('Failed to update setting. Please try again.');
    }
  }
};
```

### Return Processing Errors

```typescript
const handleReturnError = (error: any) => {
  if (error.response?.data?.detail) {
    const detail = error.response.data.detail;
    
    if (detail.includes('already returned')) {
      toast.error('These items have already been returned');
    } else if (detail.includes('quantity exceeds')) {
      toast.error('Return quantity exceeds available quantity');
    } else {
      toast.error(detail);
    }
  } else {
    toast.error('Failed to process return. Please try again.');
  }
};
```

---

## Testing Strategies

### 1. Mock System Settings

```typescript
// Mock settings for testing
const mockSystemSettings = {
  rental_status_check_enabled: "true",
  rental_status_check_time: "00:00",
  rental_status_log_retention_days: "365",
  task_scheduler_timezone: "UTC"
};

// Test settings component
describe('RentalStatusSettings', () => {
  it('should display current settings', () => {
    render(<RentalStatusSettings />, {
      wrapper: createWrapper({
        systemSettings: mockSystemSettings
      })
    });

    expect(screen.getByRole('switch')).toBeChecked();
    expect(screen.getByDisplayValue('00:00')).toBeInTheDocument();
    expect(screen.getByDisplayValue('365')).toBeInTheDocument();
  });

  it('should update setting on change', async () => {
    const updateSetting = jest.fn();
    render(<RentalStatusSettings onUpdate={updateSetting} />);

    const toggle = screen.getByRole('switch');
    await userEvent.click(toggle);

    expect(updateSetting).toHaveBeenCalledWith(
      'rental_status_check_enabled',
      'false'
    );
  });
});
```

### 2. Test Status Display

```typescript
describe('StatusBadge', () => {
  it.each([
    ['ACTIVE', 'Active', 'green'],
    ['LATE', 'Late', 'red'],
    ['PARTIAL_RETURN', 'Partial Return', 'orange'],
    ['COMPLETED', 'Completed', 'gray']
  ])('should render %s status correctly', (status, label, color) => {
    render(<StatusBadge status={status} />);
    
    const badge = screen.getByText(label);
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass(`badge-${color}`);
  });
});
```

### 3. Integration Tests

```typescript
describe('Return Flow Integration', () => {
  it('should update status after return', async () => {
    const transactionId = 'test-transaction-id';
    
    // Mock initial transaction with ACTIVE status
    server.use(
      rest.get(`/api/transactions/${transactionId}`, (req, res, ctx) => {
        return res(ctx.json({
          id: transactionId,
          current_rental_status: 'ACTIVE',
          transaction_lines: [
            { id: 'line-1', current_rental_status: 'ACTIVE' }
          ]
        }));
      })
    );

    render(<ProcessReturn transactionId={transactionId} />);
    
    // Process return
    await userEvent.click(screen.getByText('Process Return'));
    
    // Wait for status update
    await waitFor(() => {
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
    });
  });
});
```

---

## Summary

The rental status feature operates transparently in the background, automatically calculating and updating statuses during return transactions and scheduled checks. Frontend integration focuses on:

1. **Configuration**: Providing UI for system settings management
2. **Display**: Showing current status from transaction data
3. **Returns**: Processing returns that trigger automatic status updates
4. **No Direct API**: Status is managed internally, not via API calls

Remember:
- Always fetch status from transaction endpoints
- Provide clear UI for system settings configuration
- Handle return flows that trigger status updates
- Display status changes in real-time after returns
- Test settings configuration and status display thoroughly

For additional support or questions, contact the backend team.