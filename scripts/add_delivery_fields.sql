-- Add delivery and pickup fields to transaction_headers table if they don't exist

DO $$ 
BEGIN
    -- Add delivery_required column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='delivery_required') THEN
        ALTER TABLE transaction_headers ADD COLUMN delivery_required BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add delivery_address column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='delivery_address') THEN
        ALTER TABLE transaction_headers ADD COLUMN delivery_address TEXT;
    END IF;

    -- Add delivery_date column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='delivery_date') THEN
        ALTER TABLE transaction_headers ADD COLUMN delivery_date DATE;
    END IF;

    -- Add delivery_time column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='delivery_time') THEN
        ALTER TABLE transaction_headers ADD COLUMN delivery_time TIME;
    END IF;

    -- Add pickup_required column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='pickup_required') THEN
        ALTER TABLE transaction_headers ADD COLUMN pickup_required BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add pickup_date column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='pickup_date') THEN
        ALTER TABLE transaction_headers ADD COLUMN pickup_date DATE;
    END IF;

    -- Add pickup_time column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='pickup_time') THEN
        ALTER TABLE transaction_headers ADD COLUMN pickup_time TIME;
    END IF;

    -- Add other missing columns
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='payment_status') THEN
        ALTER TABLE transaction_headers ADD COLUMN payment_status VARCHAR(20);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='current_rental_status') THEN
        ALTER TABLE transaction_headers ADD COLUMN current_rental_status VARCHAR(30);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='rental_start_date') THEN
        ALTER TABLE transaction_headers ADD COLUMN rental_start_date DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='rental_end_date') THEN
        ALTER TABLE transaction_headers ADD COLUMN rental_end_date DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='rental_period') THEN
        ALTER TABLE transaction_headers ADD COLUMN rental_period INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='rental_period_unit') THEN
        ALTER TABLE transaction_headers ADD COLUMN rental_period_unit VARCHAR(10);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='transaction_headers' AND column_name='actual_return_date') THEN
        ALTER TABLE transaction_headers ADD COLUMN actual_return_date DATE;
    END IF;
END $$;