#!/usr/bin/env python3
"""
Script to clear all demo/test data from the SQLite database
This will remove:
- All trips
- All routes  
- All bookings
- All customers
- All seat blocks
- All route operator assignments
- All operator locations

This will preserve:
- Operators (bus companies)
- Bus types (VIP, Regular)
- Operator bus type configurations
"""

from app import app
from models import (
    db, Trip, Route, Booking, Customer, SeatBlock, 
    RouteOperatorAssignment, OperatorLocation, Operator, BusType, OperatorBusType
)
import sys

def clear_demo_data():
    """Clear all demo data from the database"""
    with app.app_context():
        print("🧹 Clearing Demo Data from Database...")
        print("=" * 50)
        
        # Count data before deletion
        print("📊 Current database contents:")
        trips_count = Trip.query.count()
        routes_count = Route.query.count()
        bookings_count = Booking.query.count()
        customers_count = Customer.query.count()
        seat_blocks_count = SeatBlock.query.count()
        route_assignments_count = RouteOperatorAssignment.query.count()
        operator_locations_count = OperatorLocation.query.count()
        
        print(f"  Trips: {trips_count}")
        print(f"  Routes: {routes_count}")
        print(f"  Bookings: {bookings_count}")
        print(f"  Customers: {customers_count}")
        print(f"  Seat Blocks: {seat_blocks_count}")
        print(f"  Route Assignments: {route_assignments_count}")
        print(f"  Operator Locations: {operator_locations_count}")
        
        # What we'll preserve
        operators_count = Operator.query.count()
        bus_types_count = BusType.query.count()
        operator_bus_types_count = OperatorBusType.query.count()
        
        print(f"\n🔒 Will preserve:")
        print(f"  Operators: {operators_count}")
        print(f"  Bus Types: {bus_types_count}")
        print(f"  Operator Bus Type Configs: {operator_bus_types_count}")
        
        if trips_count == 0 and routes_count == 0 and bookings_count == 0:
            print("\n✅ Database is already clean!")
            return True
        
        # Confirm deletion
        print(f"\n⚠️  This will permanently delete all demo data!")
        confirm = input("Are you sure you want to continue? (yes/no): ")
        
        if confirm.lower() not in ['yes', 'y']:
            print("❌ Operation cancelled by user")
            return False
        
        try:
            print("\n🗑️  Deleting data...")
            
            # Delete in correct order to avoid foreign key constraints
            
            # 1. Delete seat blocks first (they reference trips)
            if seat_blocks_count > 0:
                print(f"  Deleting {seat_blocks_count} seat blocks...")
                SeatBlock.query.delete()
            
            # 2. Delete bookings (they reference trips and customers)
            if bookings_count > 0:
                print(f"  Deleting {bookings_count} bookings...")
                Booking.query.delete()
            
            # 3. Delete trips (they reference routes and operators)
            if trips_count > 0:
                print(f"  Deleting {trips_count} trips...")
                Trip.query.delete()
            
            # 4. Delete route operator assignments (they reference routes and operators)
            if route_assignments_count > 0:
                print(f"  Deleting {route_assignments_count} route assignments...")
                RouteOperatorAssignment.query.delete()
            
            # 5. Delete operator locations (they reference operators)
            if operator_locations_count > 0:
                print(f"  Deleting {operator_locations_count} operator locations...")
                OperatorLocation.query.delete()
            
            # 6. Delete routes
            if routes_count > 0:
                print(f"  Deleting {routes_count} routes...")
                Route.query.delete()
            
            # 7. Delete customers (no foreign key dependencies)
            if customers_count > 0:
                print(f"  Deleting {customers_count} customers...")
                Customer.query.delete()
            
            # Commit all changes
            db.session.commit()
            
            print("\n✅ Demo data cleared successfully!")
            
            # Verify deletion
            print("\n📊 Database after cleanup:")
            print(f"  Trips: {Trip.query.count()}")
            print(f"  Routes: {Route.query.count()}")
            print(f"  Bookings: {Booking.query.count()}")
            print(f"  Customers: {Customer.query.count()}")
            print(f"  Seat Blocks: {SeatBlock.query.count()}")
            print(f"  Route Assignments: {RouteOperatorAssignment.query.count()}")
            print(f"  Operator Locations: {OperatorLocation.query.count()}")
            
            print(f"\n🔒 Preserved system data:")
            print(f"  Operators: {Operator.query.count()}")
            print(f"  Bus Types: {BusType.query.count()}")
            print(f"  Operator Bus Type Configs: {OperatorBusType.query.count()}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error clearing data: {str(e)}")
            db.session.rollback()
            return False

def reset_database_ids():
    """Reset auto-increment IDs to start from 1 again"""
    with app.app_context():
        try:
            print("\n🔄 Resetting auto-increment IDs...")
            
            # Reset SQLite auto-increment counters
            tables = [
                'trip', 'route', 'booking', 'customer', 
                'seat_block', 'route_operator_assignment', 'operator_location'
            ]
            
            for table in tables:
                try:
                    db.session.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
                except:
                    pass  # Table might not exist in sqlite_sequence
            
            db.session.commit()
            print("✅ Auto-increment IDs reset successfully!")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not reset auto-increment IDs: {str(e)}")

if __name__ == '__main__':
    print("🚀 Demo Data Cleanup Tool")
    print("=" * 60)
    
    success = clear_demo_data()
    
    if success:
        reset_database_ids()
        print("\n🎉 Database cleanup completed successfully!")
        print("\n📝 Summary:")
        print("  ✅ All demo data removed")
        print("  ✅ System configuration preserved")
        print("  ✅ Database ready for production use")
        sys.exit(0)
    else:
        print("\n❌ Database cleanup failed!")
        sys.exit(1)