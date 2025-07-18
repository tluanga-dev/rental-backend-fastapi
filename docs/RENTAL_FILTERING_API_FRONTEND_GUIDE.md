# Rental Filtering API - Frontend Implementation Guide

## Table of Contents
1. [API Overview](#api-overview)
2. [TypeScript Interfaces & Types](#typescript-interfaces--types)
3. [API Service Implementation](#api-service-implementation)
4. [React Implementation Examples](#react-implementation-examples)
5. [UI Component Examples](#ui-component-examples)
6. [State Management](#state-management)
7. [Advanced Features](#advanced-features)
8. [Testing Guide](#testing-guide)
9. [Common Use Cases](#common-use-cases)
10. [Performance Optimization](#performance-optimization)
11. [Troubleshooting](#troubleshooting)

## API Overview

### Endpoint Details
```
GET /api/transactions/rentals
```

### Base Configuration
```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const RENTALS_ENDPOINT = `${API_BASE_URL}/transactions/rentals`;
```

### Authentication
All requests require JWT authentication token in the Authorization header:
```typescript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

### Response Format
The API returns an array of rental transaction objects with embedded lifecycle information. Each object includes transaction details, rental-specific fields, and current lifecycle status.

## TypeScript Interfaces & Types

### Enums
```typescript
// Transaction Status Enum
export enum TransactionStatus {
  DRAFT = 'DRAFT',
  CONFIRMED = 'CONFIRMED',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
  REFUNDED = 'REFUNDED'
}

// Rental Status Enum
export enum RentalStatus {
  ACTIVE = 'ACTIVE',
  LATE = 'LATE',
  EXTENDED = 'EXTENDED',
  PARTIAL_RETURN = 'PARTIAL_RETURN',
  LATE_PARTIAL_RETURN = 'LATE_PARTIAL_RETURN',
  COMPLETED = 'COMPLETED'
}

// Rental Period Unit Enum
export enum RentalPeriodUnit {
  HOUR = 'HOUR',
  DAY = 'DAY',
  WEEK = 'WEEK',
  MONTH = 'MONTH'
}
```

### Query Parameters Interface
```typescript
export interface RentalFilterParams {
  // Pagination
  skip?: number;              // Default: 0, min: 0
  limit?: number;             // Default: 100, min: 1, max: 1000
  
  // Filters
  customer_id?: string;       // UUID format
  location_id?: string;       // UUID format
  status?: TransactionStatus;
  rental_status?: RentalStatus;
  date_from?: string;         // ISO date format (YYYY-MM-DD)
  date_to?: string;           // ISO date format (YYYY-MM-DD)
  overdue_only?: boolean;     // Default: false
}
```

### Response Interfaces
```typescript
export interface RentalLifecycle {
  id: string;
  transaction_id: string;
  current_status: RentalStatus;
  last_status_change: string;  // ISO datetime
  total_returned_quantity: number;
  expected_return_date: string;  // ISO date
  actual_return_date?: string;   // ISO date
  total_late_fees: number;
  total_damage_fees: number;
  total_other_fees: number;
  created_at: string;
  updated_at: string;
}

export interface RentalTransaction {
  // Core transaction fields
  id: string;
  transaction_number: string;
  transaction_date: string;     // ISO datetime
  customer_id: string;
  location_id: string;
  status: TransactionStatus;
  
  // Rental-specific fields
  rental_start_date: string;    // ISO date
  rental_end_date: string;      // ISO date
  rental_period?: number;
  rental_period_unit?: RentalPeriodUnit;
  current_rental_status: RentalStatus;
  
  // Financial fields
  total_amount: number;
  paid_amount: number;
  deposit_amount?: number;
  deposit_paid: boolean;
  customer_advance_balance: number;
  
  // Delivery/Pickup fields
  delivery_required: boolean;
  delivery_address?: string;
  delivery_date?: string;       // ISO date
  delivery_time?: string;       // HH:MM:SS format
  pickup_required: boolean;
  pickup_date?: string;         // ISO date
  pickup_time?: string;         // HH:MM:SS format
  
  // Relationships
  lifecycle?: RentalLifecycle;
  
  // Computed properties (frontend can calculate)
  is_overdue?: boolean;
  days_overdue?: number;
  reference_number?: string;    // Alias for transaction_number
  
  // Metadata
  created_at: string;
  updated_at: string;
}

export interface RentalApiResponse {
  data: RentalTransaction[];
  total?: number;
  page?: number;
  pageSize?: number;
}
```

## API Service Implementation

### Base API Service
```typescript
import axios, { AxiosInstance } from 'axios';
import { getAccessToken } from '@/utils/auth';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
      timeout: 30000,
    });

    // Request interceptor for auth
    this.api.interceptors.request.use(
      (config) => {
        const token = getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Handle token refresh or redirect to login
          await this.refreshToken();
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken() {
    // Implement token refresh logic
  }

  public getAxiosInstance() {
    return this.api;
  }
}

export const apiService = new ApiService();
```

### Rental Service
```typescript
import { apiService } from './api-service';
import { RentalTransaction, RentalFilterParams } from '@/types/rental';

export class RentalService {
  private buildQueryString(params: RentalFilterParams): string {
    const queryParams = new URLSearchParams();
    
    // Add each parameter if it exists
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.customer_id) queryParams.append('customer_id', params.customer_id);
    if (params.location_id) queryParams.append('location_id', params.location_id);
    if (params.status) queryParams.append('status', params.status);
    if (params.rental_status) queryParams.append('rental_status', params.rental_status);
    if (params.date_from) queryParams.append('date_from', params.date_from);
    if (params.date_to) queryParams.append('date_to', params.date_to);
    if (params.overdue_only !== undefined) queryParams.append('overdue_only', params.overdue_only.toString());
    
    return queryParams.toString();
  }

  async getRentals(filters: RentalFilterParams = {}): Promise<RentalTransaction[]> {
    try {
      const queryString = this.buildQueryString(filters);
      const response = await apiService.getAxiosInstance().get(
        `/transactions/rentals${queryString ? `?${queryString}` : ''}`
      );
      
      return response.data;
    } catch (error) {
      console.error('Error fetching rentals:', error);
      throw error;
    }
  }

  async getRentalById(rentalId: string): Promise<RentalTransaction> {
    try {
      const response = await apiService.getAxiosInstance().get(
        `/transactions/${rentalId}`
      );
      return response.data;
    } catch (error) {
      console.error('Error fetching rental details:', error);
      throw error;
    }
  }

  async exportRentals(filters: RentalFilterParams, format: 'csv' | 'excel' = 'csv'): Promise<Blob> {
    try {
      const queryString = this.buildQueryString(filters);
      const response = await apiService.getAxiosInstance().get(
        `/transactions/rentals/export?format=${format}&${queryString}`,
        { responseType: 'blob' }
      );
      return response.data;
    } catch (error) {
      console.error('Error exporting rentals:', error);
      throw error;
    }
  }
}

export const rentalService = new RentalService();
```

## React Implementation Examples

### Custom Hook for Rental Fetching
```typescript
import { useState, useEffect, useCallback } from 'react';
import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { rentalService } from '@/services/rental-service';
import { RentalTransaction, RentalFilterParams } from '@/types/rental';
import { useDebounce } from '@/hooks/useDebounce';

export interface UseRentalsOptions extends RentalFilterParams {
  enabled?: boolean;
  refetchInterval?: number;
}

export const useRentals = (options: UseRentalsOptions = {}) => {
  const { enabled = true, refetchInterval, ...filters } = options;
  
  // Debounce filters to avoid excessive API calls
  const debouncedFilters = useDebounce(filters, 300);
  
  const query = useQuery({
    queryKey: ['rentals', debouncedFilters],
    queryFn: () => rentalService.getRentals(debouncedFilters),
    enabled,
    refetchInterval,
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });

  return {
    ...query,
    rentals: query.data || [],
    totalCount: query.data?.length || 0,
  };
};

// Hook for single rental with lifecycle polling
export const useRental = (rentalId: string, options: { pollingInterval?: number } = {}) => {
  const { pollingInterval = 30000 } = options; // Default 30 seconds
  
  return useQuery({
    queryKey: ['rental', rentalId],
    queryFn: () => rentalService.getRentalById(rentalId),
    enabled: !!rentalId,
    refetchInterval: pollingInterval,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
};

// Hook for pagination
export const usePaginatedRentals = (initialPage = 1, pageSize = 20) => {
  const [page, setPage] = useState(initialPage);
  const [filters, setFilters] = useState<RentalFilterParams>({});
  
  const skip = (page - 1) * pageSize;
  
  const { rentals, isLoading, error, refetch } = useRentals({
    ...filters,
    skip,
    limit: pageSize,
  });
  
  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);
  
  const handleFilterChange = useCallback((newFilters: RentalFilterParams) => {
    setFilters(newFilters);
    setPage(1); // Reset to first page on filter change
  }, []);
  
  return {
    rentals,
    page,
    pageSize,
    isLoading,
    error,
    setPage: handlePageChange,
    setFilters: handleFilterChange,
    refetch,
  };
};
```

### Filter Component
```typescript
import React, { useState, useCallback } from 'react';
import { Calendar, Search, Filter, X } from 'lucide-react';
import { RentalFilterParams, TransactionStatus, RentalStatus } from '@/types/rental';
import { CustomerSelect } from '@/components/CustomerSelect';
import { LocationSelect } from '@/components/LocationSelect';
import { DateRangePicker } from '@/components/DateRangePicker';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';

interface RentalFiltersProps {
  onFiltersChange: (filters: RentalFilterParams) => void;
  initialFilters?: RentalFilterParams;
  showAdvanced?: boolean;
}

export const RentalFilters: React.FC<RentalFiltersProps> = ({
  onFiltersChange,
  initialFilters = {},
  showAdvanced = true,
}) => {
  const [filters, setFilters] = useState<RentalFilterParams>(initialFilters);
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);
  
  const handleFilterChange = useCallback((key: keyof RentalFilterParams, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange(newFilters);
  }, [filters, onFiltersChange]);
  
  const handleClearFilters = useCallback(() => {
    setFilters({});
    onFiltersChange({});
  }, [onFiltersChange]);
  
  const activeFilterCount = Object.keys(filters).filter(key => 
    filters[key as keyof RentalFilterParams] !== undefined
  ).length;
  
  return (
    <div className="space-y-4 p-4 bg-white rounded-lg shadow">
      {/* Main Filters Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {/* Customer Filter */}
        <div className="space-y-2">
          <Label htmlFor="customer">Customer</Label>
          <CustomerSelect
            value={filters.customer_id}
            onChange={(value) => handleFilterChange('customer_id', value)}
            placeholder="All Customers"
            allowClear
          />
        </div>
        
        {/* Location Filter */}
        <div className="space-y-2">
          <Label htmlFor="location">Location</Label>
          <LocationSelect
            value={filters.location_id}
            onChange={(value) => handleFilterChange('location_id', value)}
            placeholder="All Locations"
            allowClear
          />
        </div>
        
        {/* Transaction Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="status">Transaction Status</Label>
          <Select
            value={filters.status}
            onValueChange={(value) => handleFilterChange('status', value || undefined)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Statuses</SelectItem>
              {Object.values(TransactionStatus).map((status) => (
                <SelectItem key={status} value={status}>
                  {status.replace('_', ' ')}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Rental Status Filter */}
        <div className="space-y-2">
          <Label htmlFor="rental-status">Rental Status</Label>
          <Select
            value={filters.rental_status}
            onValueChange={(value) => handleFilterChange('rental_status', value || undefined)}
          >
            <SelectTrigger>
              <SelectValue placeholder="All Rental Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Rental Statuses</SelectItem>
              {Object.values(RentalStatus).map((status) => (
                <SelectItem key={status} value={status}>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={status} />
                    {status.replace('_', ' ')}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      
      {/* Date Range and Overdue Filter */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 space-y-2">
          <Label>Rental Date Range</Label>
          <DateRangePicker
            startDate={filters.date_from}
            endDate={filters.date_to}
            onStartDateChange={(date) => handleFilterChange('date_from', date)}
            onEndDateChange={(date) => handleFilterChange('date_to', date)}
            placeholder="Select date range"
          />
        </div>
        
        <div className="flex items-end">
          <div className="flex items-center space-x-2">
            <Switch
              id="overdue-only"
              checked={filters.overdue_only || false}
              onCheckedChange={(checked) => handleFilterChange('overdue_only', checked)}
            />
            <Label htmlFor="overdue-only" className="cursor-pointer">
              Overdue Only
            </Label>
          </div>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-2">
          {activeFilterCount > 0 && (
            <Badge variant="secondary">
              {activeFilterCount} filter{activeFilterCount > 1 ? 's' : ''} active
            </Badge>
          )}
        </div>
        
        <div className="flex gap-2">
          {showAdvanced && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            >
              <Filter className="w-4 h-4 mr-2" />
              Advanced
            </Button>
          )}
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearFilters}
            disabled={activeFilterCount === 0}
          >
            <X className="w-4 h-4 mr-2" />
            Clear Filters
          </Button>
          
          <Button
            variant="default"
            size="sm"
            onClick={() => onFiltersChange(filters)}
          >
            <Search className="w-4 h-4 mr-2" />
            Apply Filters
          </Button>
        </div>
      </div>
      
      {/* Advanced Filters (Optional) */}
      {showAdvanced && isAdvancedOpen && (
        <div className="pt-4 border-t space-y-4">
          <h4 className="font-medium text-sm text-gray-700">Advanced Filters</h4>
          {/* Add additional advanced filters here */}
        </div>
      )}
    </div>
  );
};

// Status Badge Component
const StatusBadge: React.FC<{ status: RentalStatus }> = ({ status }) => {
  const getStatusColor = (status: RentalStatus) => {
    switch (status) {
      case RentalStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case RentalStatus.LATE:
        return 'bg-red-100 text-red-800';
      case RentalStatus.EXTENDED:
        return 'bg-blue-100 text-blue-800';
      case RentalStatus.PARTIAL_RETURN:
        return 'bg-yellow-100 text-yellow-800';
      case RentalStatus.LATE_PARTIAL_RETURN:
        return 'bg-orange-100 text-orange-800';
      case RentalStatus.COMPLETED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  return (
    <div className={`w-3 h-3 rounded-full ${getStatusColor(status)}`} />
  );
};
```

### Rental List Component
```typescript
import React, { useMemo } from 'react';
import { format, differenceInDays } from 'date-fns';
import { ChevronRight, AlertCircle, Package, Calendar, DollarSign } from 'lucide-react';
import { RentalTransaction } from '@/types/rental';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useRouter } from 'next/navigation';
import { cn } from '@/lib/utils';

interface RentalListProps {
  rentals: RentalTransaction[];
  isLoading?: boolean;
  onRentalClick?: (rental: RentalTransaction) => void;
}

export const RentalList: React.FC<RentalListProps> = ({
  rentals,
  isLoading = false,
  onRentalClick,
}) => {
  const router = useRouter();
  
  const handleRowClick = (rental: RentalTransaction) => {
    if (onRentalClick) {
      onRentalClick(rental);
    } else {
      router.push(`/rentals/${rental.id}`);
    }
  };
  
  const getStatusBadge = (rental: RentalTransaction) => {
    const isOverdue = new Date(rental.rental_end_date) < new Date() && 
                     rental.current_rental_status !== 'COMPLETED';
    
    if (isOverdue) {
      return (
        <Badge variant="destructive" className="gap-1">
          <AlertCircle className="w-3 h-3" />
          Overdue
        </Badge>
      );
    }
    
    const statusColors: Record<string, string> = {
      ACTIVE: 'default',
      LATE: 'destructive',
      EXTENDED: 'secondary',
      PARTIAL_RETURN: 'warning',
      LATE_PARTIAL_RETURN: 'destructive',
      COMPLETED: 'success',
    };
    
    return (
      <Badge variant={statusColors[rental.current_rental_status] as any}>
        {rental.current_rental_status.replace('_', ' ')}
      </Badge>
    );
  };
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };
  
  if (isLoading) {
    return <RentalListSkeleton />;
  }
  
  if (rentals.length === 0) {
    return (
      <div className="text-center py-12">
        <Package className="w-12 h-12 mx-auto text-gray-400 mb-4" />
        <p className="text-gray-500">No rentals found</p>
      </div>
    );
  }
  
  return (
    <div className="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Reference #</TableHead>
            <TableHead>Customer</TableHead>
            <TableHead>Location</TableHead>
            <TableHead>Rental Period</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead className="text-right">Balance</TableHead>
            <TableHead className="w-[50px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rentals.map((rental) => {
            const daysRemaining = differenceInDays(
              new Date(rental.rental_end_date),
              new Date()
            );
            const balance = rental.total_amount - rental.paid_amount;
            
            return (
              <TableRow
                key={rental.id}
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleRowClick(rental)}
              >
                <TableCell className="font-medium">
                  {rental.transaction_number}
                </TableCell>
                <TableCell>
                  <CustomerCell customerId={rental.customer_id} />
                </TableCell>
                <TableCell>
                  <LocationCell locationId={rental.location_id} />
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center gap-1 text-sm">
                      <Calendar className="w-4 h-4 text-gray-400" />
                      {format(new Date(rental.rental_start_date), 'MMM dd')} - 
                      {format(new Date(rental.rental_end_date), 'MMM dd, yyyy')}
                    </div>
                    {daysRemaining > 0 && rental.current_rental_status === 'ACTIVE' && (
                      <p className="text-xs text-gray-500">
                        {daysRemaining} days remaining
                      </p>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  {getStatusBadge(rental)}
                </TableCell>
                <TableCell className="text-right">
                  {formatCurrency(rental.total_amount)}
                </TableCell>
                <TableCell className="text-right">
                  <span className={cn(
                    "font-medium",
                    balance > 0 ? "text-red-600" : "text-green-600"
                  )}>
                    {formatCurrency(balance)}
                  </span>
                </TableCell>
                <TableCell>
                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

// Skeleton loader
const RentalListSkeleton: React.FC = () => (
  <div className="rounded-lg border">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Reference #</TableHead>
          <TableHead>Customer</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Rental Period</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="text-right">Amount</TableHead>
          <TableHead className="text-right">Balance</TableHead>
          <TableHead className="w-[50px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {[...Array(5)].map((_, i) => (
          <TableRow key={i}>
            <TableCell><Skeleton className="h-4 w-24" /></TableCell>
            <TableCell><Skeleton className="h-4 w-32" /></TableCell>
            <TableCell><Skeleton className="h-4 w-28" /></TableCell>
            <TableCell><Skeleton className="h-4 w-36" /></TableCell>
            <TableCell><Skeleton className="h-6 w-20" /></TableCell>
            <TableCell><Skeleton className="h-4 w-20 ml-auto" /></TableCell>
            <TableCell><Skeleton className="h-4 w-20 ml-auto" /></TableCell>
            <TableCell><Skeleton className="h-4 w-4" /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

// Customer and Location cells would fetch data from their respective stores/APIs
const CustomerCell: React.FC<{ customerId: string }> = ({ customerId }) => {
  // In real implementation, fetch customer data
  return <span>Customer {customerId.slice(0, 8)}...</span>;
};

const LocationCell: React.FC<{ locationId: string }> = ({ locationId }) => {
  // In real implementation, fetch location data
  return <span>Location {locationId.slice(0, 8)}...</span>;
};
```

## UI Component Examples

### Mobile-Responsive Card View
```typescript
import React from 'react';
import { format, differenceInDays } from 'date-fns';
import { Calendar, MapPin, User, DollarSign, AlertCircle } from 'lucide-react';
import { RentalTransaction } from '@/types/rental';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface RentalCardProps {
  rental: RentalTransaction;
  onClick?: (rental: RentalTransaction) => void;
}

export const RentalCard: React.FC<RentalCardProps> = ({ rental, onClick }) => {
  const isOverdue = new Date(rental.rental_end_date) < new Date() && 
                   rental.current_rental_status !== 'COMPLETED';
  const daysRemaining = differenceInDays(new Date(rental.rental_end_date), new Date());
  const balance = rental.total_amount - rental.paid_amount;
  
  return (
    <Card 
      className={cn(
        "cursor-pointer transition-all hover:shadow-lg",
        isOverdue && "border-red-200 bg-red-50/50"
      )}
      onClick={() => onClick?.(rental)}
    >
      <CardHeader className="pb-3">
        <div className="flex justify-between items-start">
          <CardTitle className="text-lg">{rental.transaction_number}</CardTitle>
          <RentalStatusBadge status={rental.current_rental_status} isOverdue={isOverdue} />
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Customer Info */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <User className="w-4 h-4" />
          <span>Customer #{rental.customer_id.slice(0, 8)}</span>
        </div>
        
        {/* Location Info */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <MapPin className="w-4 h-4" />
          <span>Location #{rental.location_id.slice(0, 8)}</span>
        </div>
        
        {/* Rental Period */}
        <div className="flex items-center gap-2 text-sm">
          <Calendar className="w-4 h-4 text-gray-400" />
          <span>
            {format(new Date(rental.rental_start_date), 'MMM dd')} - 
            {format(new Date(rental.rental_end_date), 'MMM dd, yyyy')}
          </span>
        </div>
        
        {/* Days Remaining / Overdue */}
        {rental.current_rental_status === 'ACTIVE' && (
          <div className={cn(
            "text-sm font-medium",
            isOverdue ? "text-red-600" : daysRemaining <= 3 ? "text-yellow-600" : "text-gray-600"
          )}>
            {isOverdue ? (
              <span className="flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {Math.abs(daysRemaining)} days overdue
              </span>
            ) : (
              <span>{daysRemaining} days remaining</span>
            )}
          </div>
        )}
        
        {/* Financial Summary */}
        <div className="pt-3 border-t">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Amount</span>
            <span className="font-medium">${rental.total_amount.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm mt-1">
            <span className="text-gray-600">Balance Due</span>
            <span className={cn(
              "font-medium",
              balance > 0 ? "text-red-600" : "text-green-600"
            )}>
              ${balance.toFixed(2)}
            </span>
          </div>
        </div>
        
        {/* Lifecycle Info */}
        {rental.lifecycle && (
          <div className="pt-3 border-t text-xs text-gray-500">
            Last updated: {format(new Date(rental.lifecycle.last_status_change), 'MMM dd, yyyy h:mm a')}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const RentalStatusBadge: React.FC<{ status: string; isOverdue?: boolean }> = ({ 
  status, 
  isOverdue = false 
}) => {
  if (isOverdue) {
    return (
      <Badge variant="destructive" className="gap-1">
        <AlertCircle className="w-3 h-3" />
        Overdue
      </Badge>
    );
  }
  
  const variants: Record<string, any> = {
    ACTIVE: 'default',
    LATE: 'destructive',
    EXTENDED: 'secondary',
    PARTIAL_RETURN: 'warning',
    COMPLETED: 'success',
  };
  
  return (
    <Badge variant={variants[status] || 'default'}>
      {status.replace('_', ' ')}
    </Badge>
  );
};
```

### Dashboard Widget
```typescript
import React from 'react';
import { ArrowUp, ArrowDown, Package, AlertTriangle, Clock, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useRentals } from '@/hooks/useRentals';
import { RentalStatus } from '@/types/rental';
import { Skeleton } from '@/components/ui/skeleton';

export const RentalDashboardWidget: React.FC = () => {
  const { rentals, isLoading } = useRentals({ limit: 1000 }); // Get all for stats
  
  const stats = React.useMemo(() => {
    if (!rentals.length) return null;
    
    const active = rentals.filter(r => r.current_rental_status === RentalStatus.ACTIVE);
    const overdue = rentals.filter(r => {
      const isOverdue = new Date(r.rental_end_date) < new Date();
      return isOverdue && r.current_rental_status !== RentalStatus.COMPLETED;
    });
    const completed = rentals.filter(r => r.current_rental_status === RentalStatus.COMPLETED);
    
    const totalRevenue = rentals.reduce((sum, r) => sum + r.total_amount, 0);
    const totalOutstanding = rentals.reduce((sum, r) => sum + (r.total_amount - r.paid_amount), 0);
    
    return {
      total: rentals.length,
      active: active.length,
      overdue: overdue.length,
      completed: completed.length,
      totalRevenue,
      totalOutstanding,
    };
  }, [rentals]);
  
  if (isLoading) {
    return <DashboardSkeleton />;
  }
  
  if (!stats) {
    return null;
  }
  
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Rentals</CardTitle>
          <Package className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total}</div>
          <p className="text-xs text-muted-foreground">
            +12% from last month
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Rentals</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.active}</div>
          <div className="flex items-center text-xs text-green-600">
            <ArrowUp className="h-3 w-3 mr-1" />
            8% increase
          </div>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Overdue</CardTitle>
          <AlertTriangle className="h-4 w-4 text-destructive" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-destructive">{stats.overdue}</div>
          <p className="text-xs text-muted-foreground">
            Requires immediate attention
          </p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Outstanding Balance</CardTitle>
          <DollarSign className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            ${stats.totalOutstanding.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground">
            Across all active rentals
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

const DashboardSkeleton: React.FC = () => (
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
    {[...Array(4)].map((_, i) => (
      <Card key={i}>
        <CardHeader className="space-y-0 pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-16 mb-2" />
          <Skeleton className="h-3 w-32" />
        </CardContent>
      </Card>
    ))}
  </div>
);
```

## State Management

### Zustand Store Implementation
```typescript
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { RentalFilterParams, RentalTransaction } from '@/types/rental';
import { rentalService } from '@/services/rental-service';

interface RentalState {
  // State
  rentals: RentalTransaction[];
  filters: RentalFilterParams;
  selectedRental: RentalTransaction | null;
  isLoading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  
  // Actions
  setFilters: (filters: RentalFilterParams) => void;
  setSelectedRental: (rental: RentalTransaction | null) => void;
  fetchRentals: () => Promise<void>;
  refreshRentals: () => Promise<void>;
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  clearFilters: () => void;
}

export const useRentalStore = create<RentalState>()(
  persist(
    (set, get) => ({
      // Initial state
      rentals: [],
      filters: {},
      selectedRental: null,
      isLoading: false,
      error: null,
      totalCount: 0,
      currentPage: 1,
      pageSize: 20,
      
      // Actions
      setFilters: (filters) => {
        set({ filters, currentPage: 1 });
        get().fetchRentals();
      },
      
      setSelectedRental: (rental) => set({ selectedRental: rental }),
      
      fetchRentals: async () => {
        const { filters, currentPage, pageSize } = get();
        
        set({ isLoading: true, error: null });
        
        try {
          const skip = (currentPage - 1) * pageSize;
          const rentals = await rentalService.getRentals({
            ...filters,
            skip,
            limit: pageSize,
          });
          
          set({ 
            rentals, 
            totalCount: rentals.length, // In real app, get from API response
            isLoading: false 
          });
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch rentals',
            isLoading: false 
          });
        }
      },
      
      refreshRentals: async () => {
        await get().fetchRentals();
      },
      
      setPage: (page) => {
        set({ currentPage: page });
        get().fetchRentals();
      },
      
      setPageSize: (size) => {
        set({ pageSize: size, currentPage: 1 });
        get().fetchRentals();
      },
      
      clearFilters: () => {
        set({ filters: {}, currentPage: 1 });
        get().fetchRentals();
      },
    }),
    {
      name: 'rental-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ 
        filters: state.filters,
        pageSize: state.pageSize,
      }),
    }
  )
);

// Selectors
export const useRentalFilters = () => useRentalStore(state => state.filters);
export const useSelectedRental = () => useRentalStore(state => state.selectedRental);
export const useRentalPagination = () => useRentalStore(state => ({
  currentPage: state.currentPage,
  pageSize: state.pageSize,
  totalCount: state.totalCount,
  setPage: state.setPage,
  setPageSize: state.setPageSize,
}));
```

## Advanced Features

### Real-time Updates with WebSocket
```typescript
import { useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { RentalTransaction } from '@/types/rental';

interface RentalUpdateEvent {
  type: 'created' | 'updated' | 'deleted';
  rental: RentalTransaction;
}

export const useRentalWebSocket = () => {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  
  useEffect(() => {
    const ws = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/rentals');
    
    ws.onopen = () => {
      console.log('Connected to rental updates');
    };
    
    ws.onmessage = (event) => {
      const update: RentalUpdateEvent = JSON.parse(event.data);
      
      switch (update.type) {
        case 'created':
        case 'updated':
          // Update specific rental in cache
          queryClient.setQueryData(['rental', update.rental.id], update.rental);
          
          // Invalidate rental list to refetch
          queryClient.invalidateQueries({ queryKey: ['rentals'] });
          break;
          
        case 'deleted':
          // Remove from cache
          queryClient.removeQueries({ queryKey: ['rental', update.rental.id] });
          queryClient.invalidateQueries({ queryKey: ['rentals'] });
          break;
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    wsRef.current = ws;
    
    return () => {
      ws.close();
    };
  }, [queryClient]);
  
  return wsRef.current;
};

// Usage in component
export const RentalDashboard: React.FC = () => {
  useRentalWebSocket(); // Enable real-time updates
  
  // Rest of component...
};
```

### Export Functionality
```typescript
import { useState } from 'react';
import { Download, FileSpreadsheet, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/ui/use-toast';
import { rentalService } from '@/services/rental-service';
import { RentalFilterParams } from '@/types/rental';

interface ExportButtonProps {
  filters: RentalFilterParams;
}

export const ExportButton: React.FC<ExportButtonProps> = ({ filters }) => {
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();
  
  const handleExport = async (format: 'csv' | 'excel') => {
    setIsExporting(true);
    
    try {
      const blob = await rentalService.exportRentals(filters, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rentals_export_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      toast({
        title: 'Export Successful',
        description: `Rentals exported to ${format.toUpperCase()} format`,
      });
    } catch (error) {
      toast({
        title: 'Export Failed',
        description: 'Failed to export rentals. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" disabled={isExporting}>
          <Download className="w-4 h-4 mr-2" />
          {isExporting ? 'Exporting...' : 'Export'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={() => handleExport('csv')}>
          <FileText className="w-4 h-4 mr-2" />
          Export as CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleExport('excel')}>
          <FileSpreadsheet className="w-4 h-4 mr-2" />
          Export as Excel
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

### Virtual Scrolling for Large Lists
```typescript
import React from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';
import { RentalTransaction } from '@/types/rental';
import { RentalCard } from './RentalCard';

interface VirtualRentalListProps {
  rentals: RentalTransaction[];
  onRentalClick?: (rental: RentalTransaction) => void;
}

export const VirtualRentalList: React.FC<VirtualRentalListProps> = ({
  rentals,
  onRentalClick,
}) => {
  const parentRef = React.useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: rentals.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // Estimated height of each rental card
    overscan: 5, // Render 5 items outside of view
  });
  
  return (
    <div
      ref={parentRef}
      className="h-[600px] overflow-auto"
      style={{
        contain: 'strict',
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const rental = rentals[virtualItem.index];
          
          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <div className="p-2">
                <RentalCard
                  rental={rental}
                  onClick={onRentalClick}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
```

## Testing Guide

### Unit Tests
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RentalFilters } from '@/components/RentalFilters';
import { rentalService } from '@/services/rental-service';

jest.mock('@/services/rental-service');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('RentalFilters', () => {
  it('should render all filter inputs', () => {
    const onFiltersChange = jest.fn();
    
    render(
      <RentalFilters onFiltersChange={onFiltersChange} />,
      { wrapper: createWrapper() }
    );
    
    expect(screen.getByLabelText('Customer')).toBeInTheDocument();
    expect(screen.getByLabelText('Location')).toBeInTheDocument();
    expect(screen.getByLabelText('Transaction Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Rental Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Overdue Only')).toBeInTheDocument();
  });
  
  it('should call onFiltersChange when filters are applied', async () => {
    const onFiltersChange = jest.fn();
    
    render(
      <RentalFilters onFiltersChange={onFiltersChange} />,
      { wrapper: createWrapper() }
    );
    
    // Toggle overdue only
    const overdueSwitch = screen.getByLabelText('Overdue Only');
    fireEvent.click(overdueSwitch);
    
    // Apply filters
    const applyButton = screen.getByText('Apply Filters');
    fireEvent.click(applyButton);
    
    await waitFor(() => {
      expect(onFiltersChange).toHaveBeenCalledWith({
        overdue_only: true,
      });
    });
  });
  
  it('should clear all filters', () => {
    const onFiltersChange = jest.fn();
    
    render(
      <RentalFilters 
        onFiltersChange={onFiltersChange}
        initialFilters={{ overdue_only: true, status: 'CONFIRMED' }}
      />,
      { wrapper: createWrapper() }
    );
    
    const clearButton = screen.getByText('Clear Filters');
    fireEvent.click(clearButton);
    
    expect(onFiltersChange).toHaveBeenCalledWith({});
  });
});
```

### Integration Tests
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useRentals } from '@/hooks/useRentals';
import { rentalService } from '@/services/rental-service';
import { mockRentals } from '@/test/mocks/rentals';

jest.mock('@/services/rental-service');

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useRentals', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should fetch rentals with filters', async () => {
    const mockGetRentals = rentalService.getRentals as jest.Mock;
    mockGetRentals.mockResolvedValue(mockRentals);
    
    const { result } = renderHook(
      () => useRentals({ customer_id: '123', overdue_only: true }),
      { wrapper: createWrapper() }
    );
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    expect(mockGetRentals).toHaveBeenCalledWith({
      customer_id: '123',
      overdue_only: true,
    });
    
    expect(result.current.rentals).toEqual(mockRentals);
    expect(result.current.totalCount).toBe(mockRentals.length);
  });
  
  it('should handle errors gracefully', async () => {
    const mockError = new Error('API Error');
    const mockGetRentals = rentalService.getRentals as jest.Mock;
    mockGetRentals.mockRejectedValue(mockError);
    
    const { result } = renderHook(
      () => useRentals(),
      { wrapper: createWrapper() }
    );
    
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });
    
    expect(result.current.error).toBe(mockError);
    expect(result.current.rentals).toEqual([]);
  });
});
```

### Mock Data Generator
```typescript
import { faker } from '@faker-js/faker';
import { RentalTransaction, TransactionStatus, RentalStatus } from '@/types/rental';

export const generateMockRental = (overrides?: Partial<RentalTransaction>): RentalTransaction => {
  const startDate = faker.date.recent({ days: 30 });
  const endDate = faker.date.future({ years: 0.1, refDate: startDate });
  const totalAmount = faker.number.float({ min: 100, max: 5000, precision: 0.01 });
  const paidAmount = faker.number.float({ min: 0, max: totalAmount, precision: 0.01 });
  
  return {
    id: faker.string.uuid(),
    transaction_number: `REN-${faker.date.recent().toISOString().split('T')[0].replace(/-/g, '')}-${faker.number.int({ min: 1000, max: 9999 })}`,
    transaction_date: faker.date.recent().toISOString(),
    customer_id: faker.string.uuid(),
    location_id: faker.string.uuid(),
    status: faker.helpers.arrayElement(Object.values(TransactionStatus)),
    rental_start_date: startDate.toISOString().split('T')[0],
    rental_end_date: endDate.toISOString().split('T')[0],
    rental_period: faker.number.int({ min: 1, max: 30 }),
    rental_period_unit: 'DAY',
    current_rental_status: faker.helpers.arrayElement(Object.values(RentalStatus)),
    total_amount: totalAmount,
    paid_amount: paidAmount,
    deposit_amount: faker.number.float({ min: 50, max: 500, precision: 0.01 }),
    deposit_paid: faker.datatype.boolean(),
    customer_advance_balance: faker.number.float({ min: 0, max: 1000, precision: 0.01 }),
    delivery_required: faker.datatype.boolean(),
    delivery_address: faker.location.streetAddress(),
    delivery_date: faker.date.future().toISOString().split('T')[0],
    delivery_time: '10:00:00',
    pickup_required: faker.datatype.boolean(),
    pickup_date: faker.date.future().toISOString().split('T')[0],
    pickup_time: '16:00:00',
    created_at: faker.date.recent().toISOString(),
    updated_at: faker.date.recent().toISOString(),
    ...overrides,
  };
};

export const generateMockRentals = (count: number = 10): RentalTransaction[] => {
  return Array.from({ length: count }, () => generateMockRental());
};
```

## Common Use Cases

### Customer Rental History
```typescript
import React from 'react';
import { useParams } from 'next/navigation';
import { useRentals } from '@/hooks/useRentals';
import { RentalList } from '@/components/RentalList';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RentalStatus } from '@/types/rental';

export const CustomerRentalHistory: React.FC = () => {
  const { customerId } = useParams();
  
  const activeRentals = useRentals({
    customer_id: customerId as string,
    rental_status: RentalStatus.ACTIVE,
  });
  
  const overdueRentals = useRentals({
    customer_id: customerId as string,
    overdue_only: true,
  });
  
  const completedRentals = useRentals({
    customer_id: customerId as string,
    rental_status: RentalStatus.COMPLETED,
  });
  
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Rental History</h2>
      
      <Tabs defaultValue="active">
        <TabsList>
          <TabsTrigger value="active">
            Active ({activeRentals.totalCount})
          </TabsTrigger>
          <TabsTrigger value="overdue">
            Overdue ({overdueRentals.totalCount})
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed ({completedRentals.totalCount})
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="active">
          <RentalList 
            rentals={activeRentals.rentals} 
            isLoading={activeRentals.isLoading}
          />
        </TabsContent>
        
        <TabsContent value="overdue">
          <RentalList 
            rentals={overdueRentals.rentals} 
            isLoading={overdueRentals.isLoading}
          />
        </TabsContent>
        
        <TabsContent value="completed">
          <RentalList 
            rentals={completedRentals.rentals} 
            isLoading={completedRentals.isLoading}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};
```

### Overdue Rental Alerts
```typescript
import React from 'react';
import { Bell, AlertTriangle } from 'lucide-react';
import { useRentals } from '@/hooks/useRentals';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { format, differenceInDays } from 'date-fns';

export const OverdueRentalAlerts: React.FC = () => {
  const { rentals: overdueRentals, isLoading } = useRentals({
    overdue_only: true,
    limit: 10,
  });
  
  const alertCount = overdueRentals.length;
  
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          {alertCount > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-1 -right-1 h-5 w-5 p-0 flex items-center justify-center"
            >
              {alertCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              Overdue Rentals
            </h4>
            <Badge variant="destructive">{alertCount}</Badge>
          </div>
          
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : alertCount === 0 ? (
            <p className="text-sm text-muted-foreground">No overdue rentals</p>
          ) : (
            <ScrollArea className="h-[300px]">
              <div className="space-y-3">
                {overdueRentals.map((rental) => {
                  const daysOverdue = differenceInDays(
                    new Date(),
                    new Date(rental.rental_end_date)
                  );
                  
                  return (
                    <div
                      key={rental.id}
                      className="p-3 rounded-lg border bg-red-50 border-red-200 cursor-pointer hover:bg-red-100"
                      onClick={() => window.location.href = `/rentals/${rental.id}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-sm">
                            {rental.transaction_number}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Due: {format(new Date(rental.rental_end_date), 'MMM dd, yyyy')}
                          </p>
                        </div>
                        <Badge variant="destructive" className="text-xs">
                          {daysOverdue}d overdue
                        </Badge>
                      </div>
                      <p className="text-xs mt-1">
                        Balance: ${(rental.total_amount - rental.paid_amount).toFixed(2)}
                      </p>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>
          )}
          
          <Button 
            className="w-full" 
            size="sm"
            onClick={() => window.location.href = '/rentals?overdue_only=true'}
          >
            View All Overdue Rentals
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
};
```

## Performance Optimization

### Debounced Search
```typescript
import { useState, useCallback, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);
  
  return debouncedValue;
}

// Usage in search component
export const RentalSearch: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);
  
  const { rentals, isLoading } = useRentals({
    customer_name: debouncedSearch, // Assuming backend supports name search
  });
  
  return (
    <div>
      <Input
        type="search"
        placeholder="Search rentals..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      {/* Render results */}
    </div>
  );
};
```

### Query Result Caching
```typescript
import { QueryClient } from '@tanstack/react-query';

// Configure query client with optimal caching
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error instanceof Error && error.message.includes('4')) {
          return false;
        }
        return failureCount < 3;
      },
    },
  },
});

// Prefetch rentals for better UX
export const prefetchRentals = async (filters: RentalFilterParams) => {
  await queryClient.prefetchQuery({
    queryKey: ['rentals', filters],
    queryFn: () => rentalService.getRentals(filters),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};
```

### Lazy Loading Components
```typescript
import dynamic from 'next/dynamic';
import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

// Lazy load heavy components
const RentalFilters = dynamic(() => import('@/components/RentalFilters'), {
  loading: () => <Skeleton className="h-32 w-full" />,
  ssr: false, // Disable SSR for client-only components
});

const RentalList = dynamic(() => import('@/components/RentalList'), {
  loading: () => <Skeleton className="h-96 w-full" />,
});

export const RentalsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <Suspense fallback={<Skeleton className="h-32 w-full" />}>
        <RentalFilters onFiltersChange={handleFiltersChange} />
      </Suspense>
      
      <Suspense fallback={<Skeleton className="h-96 w-full" />}>
        <RentalList rentals={rentals} />
      </Suspense>
    </div>
  );
};
```

## Troubleshooting

### Common Issues and Solutions

#### 1. 422 Unprocessable Entity Errors
```typescript
// Problem: Invalid UUID format
// Solution: Validate UUIDs before sending
const isValidUUID = (uuid: string): boolean => {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
};

// Use in filter validation
if (filters.customer_id && !isValidUUID(filters.customer_id)) {
  console.error('Invalid customer ID format');
  return;
}
```

#### 2. Date Format Issues
```typescript
// Problem: Backend expects YYYY-MM-DD format
// Solution: Format dates consistently
import { format } from 'date-fns';

const formatDateForAPI = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return format(dateObj, 'yyyy-MM-dd');
};

// Usage
const filters = {
  date_from: formatDateForAPI(startDate),
  date_to: formatDateForAPI(endDate),
};
```

#### 3. Performance Issues with Large Lists
```typescript
// Problem: Rendering thousands of rentals causes lag
// Solution: Implement pagination and virtual scrolling

// Backend pagination
const PAGE_SIZE = 50;
const { rentals } = useRentals({
  skip: (currentPage - 1) * PAGE_SIZE,
  limit: PAGE_SIZE,
});

// Or use virtual scrolling (see Virtual Scrolling section above)
```

#### 4. Stale Data Issues
```typescript
// Problem: Data doesn't update after mutations
// Solution: Invalidate queries after mutations

const { mutate: updateRental } = useMutation({
  mutationFn: rentalService.updateRental,
  onSuccess: () => {
    // Invalidate and refetch
    queryClient.invalidateQueries({ queryKey: ['rentals'] });
    queryClient.invalidateQueries({ queryKey: ['rental', rentalId] });
  },
});
```

### Debug Mode
```typescript
// Enable debug logging for API calls
const DEBUG = process.env.NODE_ENV === 'development';

class ApiService {
  private logRequest(method: string, url: string, data?: any) {
    if (DEBUG) {
      console.group(`🔵 API Request: ${method} ${url}`);
      console.log('Data:', data);
      console.groupEnd();
    }
  }
  
  private logResponse(method: string, url: string, response: any) {
    if (DEBUG) {
      console.group(`🟢 API Response: ${method} ${url}`);
      console.log('Status:', response.status);
      console.log('Data:', response.data);
      console.groupEnd();
    }
  }
  
  private logError(method: string, url: string, error: any) {
    if (DEBUG) {
      console.group(`🔴 API Error: ${method} ${url}`);
      console.error('Error:', error.response || error);
      console.groupEnd();
    }
  }
}
```

### Browser Compatibility
```typescript
// Ensure compatibility with older browsers
// polyfills.ts
import 'core-js/stable';
import 'regenerator-runtime/runtime';

// Date handling for Safari
if (!Date.prototype.toISOString) {
  Date.prototype.toISOString = function() {
    return this.getUTCFullYear() +
      '-' + pad(this.getUTCMonth() + 1) +
      '-' + pad(this.getUTCDate()) +
      'T' + pad(this.getUTCHours()) +
      ':' + pad(this.getUTCMinutes()) +
      ':' + pad(this.getUTCSeconds()) +
      '.' + (this.getUTCMilliseconds() / 1000).toFixed(3).slice(2, 5) +
      'Z';
  };
}
```

## API Error Handling Reference

### Error Response Format
```typescript
interface ApiError {
  detail: string;
  status_code: number;
  timestamp?: string;
  path?: string;
}

// Handle errors consistently
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  
  switch (error.response?.status) {
    case 400:
      return 'Bad request. Please check your input.';
    case 401:
      return 'Unauthorized. Please login again.';
    case 403:
      return 'Forbidden. You do not have permission.';
    case 404:
      return 'Resource not found.';
    case 422:
      return 'Validation error. Please check your input.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return 'An unexpected error occurred.';
  }
};
```

## Conclusion

This comprehensive guide provides everything needed to implement the rental filtering API in your frontend application. The examples use React with TypeScript, but the concepts and API patterns can be adapted to other frameworks.

Key takeaways:
- Use TypeScript for type safety
- Implement proper error handling
- Optimize performance with caching and pagination
- Provide good UX with loading states and error messages
- Test thoroughly with unit and integration tests
- Monitor and debug effectively in production

For additional support or questions, refer to the backend API documentation or contact the backend team.