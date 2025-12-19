"""Tests for DatabaseWriter class

Tests the database writing functionality with transaction management
and error handling.
"""

import pytest
import os
import json
from datetime import datetime
from typing import Generator

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db_client import DatabaseWriter, DatabaseError
from shared.models import DatabaseConfig, MethodMetadata, MethodConfig, MethodParameter


# Test database configuration
TEST_DB_CONFIG = DatabaseConfig(
    host=os.getenv('TEST_DB_HOST', 'localhost'),
    port=int(os.getenv('TEST_DB_PORT', '5432')),
    database=os.getenv('TEST_DB_NAME', 'qwen_agent_test'),
    user=os.getenv('TEST_DB_USER', 'postgres'),
    password=os.getenv('TEST_DB_PASSWORD', 'postgres'),
    pool_size=2
)


@pytest.fixture
def db_writer() -> Generator[DatabaseWriter, None, None]:
    """Fixture to create and cleanup DatabaseWriter instance"""
    writer = None
    try:
        writer = DatabaseWriter(TEST_DB_CONFIG)
        writer.ensure_schema()
        yield writer
    finally:
        if writer:
            # Clean up test data
            try:
                conn = writer.db_connection.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM registered_methods;")
                conn.commit()
                cursor.close()
                writer.db_connection.return_connection(conn)
            except Exception:
                pass
            writer.close()


@pytest.fixture
def sample_method() -> MethodMetadata:
    """Fixture to create a sample method metadata"""
    return MethodMetadata(
        name="test_method",
        description="A test method",
        parameters_json='[{"name": "param1", "type": "string", "description": "Test param", "required": true, "default": null}]',
        return_type="string",
        module_path="test.module",
        function_name="test_function"
    )


@pytest.fixture
def sample_methods() -> list[MethodMetadata]:
    """Fixture to create multiple sample method metadata"""
    return [
        MethodMetadata(
            name="method_1",
            description="First test method",
            parameters_json='[{"name": "x", "type": "int", "description": "X value", "required": true, "default": null}]',
            return_type="int",
            module_path="test.module1",
            function_name="func1"
        ),
        MethodMetadata(
            name="method_2",
            description="Second test method",
            parameters_json='[{"name": "y", "type": "float", "description": "Y value", "required": true, "default": null}]',
            return_type="float",
            module_path="test.module2",
            function_name="func2"
        ),
        MethodMetadata(
            name="method_3",
            description="Third test method",
            parameters_json='[]',
            return_type="None",
            module_path="test.module3",
            function_name="func3"
        )
    ]


class TestDatabaseWriter:
    """Test suite for DatabaseWriter"""
    
    def test_initialization(self):
        """Test DatabaseWriter initialization"""
        writer = DatabaseWriter(TEST_DB_CONFIG)
        assert writer is not None
        assert writer.db_connection is not None
        writer.close()
    
    def test_ensure_schema(self, db_writer):
        """Test schema creation"""
        # Schema should already be created by fixture
        # Verify table exists by querying it
        conn = db_writer.db_connection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'registered_methods'
            );
        """)
        
        exists = cursor.fetchone()[0]
        assert exists is True
        
        cursor.close()
        db_writer.db_connection.return_connection(conn)
    
    def test_upsert_method_insert(self, db_writer, sample_method):
        """Test inserting a new method"""
        db_writer.upsert_method(sample_method)
        
        # Verify method was inserted
        retrieved = db_writer.get_method_by_name(sample_method.name)
        assert retrieved is not None
        assert retrieved.name == sample_method.name
        assert retrieved.description == sample_method.description
        assert retrieved.parameters_json == sample_method.parameters_json
        assert retrieved.return_type == sample_method.return_type
        assert retrieved.module_path == sample_method.module_path
        assert retrieved.function_name == sample_method.function_name
        assert retrieved.id is not None
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_upsert_method_update(self, db_writer, sample_method):
        """Test updating an existing method"""
        # Insert initial method
        db_writer.upsert_method(sample_method)
        
        # Get the created_at timestamp
        first_version = db_writer.get_method_by_name(sample_method.name)
        first_created_at = first_version.created_at
        
        # Update the method
        updated_method = MethodMetadata(
            name=sample_method.name,
            description="Updated description",
            parameters_json='[{"name": "new_param", "type": "int", "description": "New param", "required": false, "default": 0}]',
            return_type="int",
            module_path="updated.module",
            function_name="updated_function"
        )
        
        db_writer.upsert_method(updated_method)
        
        # Verify method was updated
        retrieved = db_writer.get_method_by_name(sample_method.name)
        assert retrieved is not None
        assert retrieved.name == updated_method.name
        assert retrieved.description == updated_method.description
        assert retrieved.parameters_json == updated_method.parameters_json
        assert retrieved.return_type == updated_method.return_type
        assert retrieved.module_path == updated_method.module_path
        assert retrieved.function_name == updated_method.function_name
        
        # created_at should remain the same
        assert retrieved.created_at == first_created_at
        
        # updated_at should be different (later)
        assert retrieved.updated_at >= first_created_at
    
    def test_upsert_methods_batch(self, db_writer, sample_methods):
        """Test batch inserting multiple methods"""
        db_writer.upsert_methods(sample_methods)
        
        # Verify all methods were inserted
        for method in sample_methods:
            retrieved = db_writer.get_method_by_name(method.name)
            assert retrieved is not None
            assert retrieved.name == method.name
            assert retrieved.description == method.description
    
    def test_upsert_methods_empty_list(self, db_writer):
        """Test upserting empty list does not raise error"""
        # Should not raise an error
        db_writer.upsert_methods([])
    
    def test_upsert_methods_transaction_rollback(self, db_writer, sample_methods):
        """Test that transaction rolls back on error"""
        # Insert first method successfully
        db_writer.upsert_method(sample_methods[0])
        
        # Create an invalid method (missing required field)
        invalid_method = MethodMetadata(
            name="invalid_method",
            description="",  # Empty description might be valid
            parameters_json='invalid json',  # This will cause an error
            return_type="string",
            module_path="test",
            function_name="test"
        )
        
        # Add invalid method to the batch
        batch_with_invalid = sample_methods[1:] + [invalid_method]
        
        # Attempt to upsert batch with invalid method
        with pytest.raises(DatabaseError):
            db_writer.upsert_methods(batch_with_invalid)
        
        # Verify that methods from failed batch were not inserted
        for method in sample_methods[1:]:
            retrieved = db_writer.get_method_by_name(method.name)
            assert retrieved is None
    
    def test_get_method_by_name_not_found(self, db_writer):
        """Test retrieving non-existent method returns None"""
        retrieved = db_writer.get_method_by_name("nonexistent_method")
        assert retrieved is None
    
    def test_upsert_method_idempotence(self, db_writer, sample_method):
        """Test that upserting the same method multiple times is idempotent"""
        # Insert method three times
        db_writer.upsert_method(sample_method)
        db_writer.upsert_method(sample_method)
        db_writer.upsert_method(sample_method)
        
        # Verify only one record exists
        conn = db_writer.db_connection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM registered_methods WHERE name = %s;",
            (sample_method.name,)
        )
        
        count = cursor.fetchone()[0]
        assert count == 1
        
        cursor.close()
        db_writer.db_connection.return_connection(conn)
    
    def test_parameters_deserialization(self, db_writer):
        """Test that parameters are correctly serialized and deserialized"""
        method_config = MethodConfig(
            name="test_params",
            description="Test parameter serialization",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="string",
                    description="First parameter",
                    required=True
                ),
                MethodParameter(
                    name="param2",
                    type="int",
                    description="Second parameter",
                    required=False,
                    default=42
                )
            ],
            return_type="dict",
            module_path="test.module",
            function_name="test_func"
        )
        
        method_metadata = MethodMetadata.from_method_config(method_config)
        db_writer.upsert_method(method_metadata)
        
        # Retrieve and verify
        retrieved = db_writer.get_method_by_name("test_params")
        assert retrieved is not None
        
        params = retrieved.parameters
        assert len(params) == 2
        assert params[0].name == "param1"
        assert params[0].type == "string"
        assert params[0].required is True
        assert params[1].name == "param2"
        assert params[1].type == "int"
        assert params[1].required is False
        assert params[1].default == 42
    
    def test_close(self, db_writer):
        """Test closing database writer"""
        # Should not raise an error
        db_writer.close()
        
        # After closing, operations should fail
        with pytest.raises(Exception):
            db_writer.db_connection.get_connection()


class TestDatabaseWriterErrors:
    """Test error handling in DatabaseWriter"""
    
    def test_invalid_database_config(self):
        """Test initialization with invalid database config"""
        invalid_config = DatabaseConfig(
            host="nonexistent_host",
            port=5432,
            database="nonexistent_db",
            user="invalid_user",
            password="invalid_password"
        )
        
        with pytest.raises(DatabaseError):
            DatabaseWriter(invalid_config)
    
    def test_upsert_with_invalid_json(self, db_writer):
        """Test upserting method with invalid JSON parameters"""
        invalid_method = MethodMetadata(
            name="invalid_json_method",
            description="Method with invalid JSON",
            parameters_json="not valid json {{{",
            return_type="string",
            module_path="test",
            function_name="test"
        )
        
        with pytest.raises(DatabaseError):
            db_writer.upsert_method(invalid_method)


class TestDatabaseWriterPropertyBased:
    """Property-based tests for DatabaseWriter using Hypothesis"""
    
    @pytest.mark.property
    def test_upsert_idempotence_property(self, db_writer):
        """
        Feature: qwen-agent-scheduler, Property 14: Upsert idempotence
        
        Property: For any method, inserting it multiple times with the same name 
        should result in exactly one database record, with the content matching 
        the most recent insert.
        
        Validates: Requirements 4.4
        """
        from hypothesis import given, strategies as st
        
        # Strategy for generating valid method names
        method_names = st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                min_codepoint=65
            ),
            min_size=2,
            max_size=50
        ).filter(lambda s: s and s[0].isalpha() and s.isidentifier())
        
        # Strategy for generating valid parameter JSON
        param_json = st.lists(
            st.fixed_dictionaries({
                'name': st.text(min_size=1, max_size=20).filter(str.isidentifier),
                'type': st.sampled_from(['string', 'int', 'float', 'bool', 'dict', 'list']),
                'description': st.text(min_size=1, max_size=100),
                'required': st.booleans(),
                'default': st.none() | st.integers() | st.text(max_size=20)
            }),
            min_size=0,
            max_size=5
        ).map(lambda params: json.dumps(params))
        
        # Strategy for generating MethodMetadata
        method_metadata_strategy = st.builds(
            MethodMetadata,
            name=method_names,
            description=st.text(min_size=1, max_size=200),
            parameters_json=param_json,
            return_type=st.sampled_from(['string', 'int', 'float', 'bool', 'dict', 'list', 'None']),
            module_path=st.text(min_size=1, max_size=50).filter(lambda s: '.' in s or s.isidentifier()),
            function_name=method_names
        )
        
        @given(
            original_method=method_metadata_strategy,
            num_inserts=st.integers(min_value=2, max_value=5)
        )
        def property_test(original_method, num_inserts):
            """Test that multiple upserts result in exactly one record"""
            # Create variations of the method with same name but different content
            methods_to_insert = []
            
            for i in range(num_inserts):
                if i == 0:
                    # First insert is the original
                    methods_to_insert.append(original_method)
                else:
                    # Subsequent inserts have same name but different content
                    modified_method = MethodMetadata(
                        name=original_method.name,
                        description=f"{original_method.description}_v{i}",
                        parameters_json=original_method.parameters_json,
                        return_type=original_method.return_type,
                        module_path=f"{original_method.module_path}_v{i}",
                        function_name=f"{original_method.function_name}_v{i}"
                    )
                    methods_to_insert.append(modified_method)
            
            # Insert all versions
            for method in methods_to_insert:
                db_writer.upsert_method(method)
            
            # Verify exactly one record exists
            conn = db_writer.db_connection.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM registered_methods WHERE name = %s;",
                    (original_method.name,)
                )
                count = cursor.fetchone()[0]
                
                # Property 1: Exactly one record should exist
                assert count == 1, f"Expected 1 record, found {count}"
                
                # Retrieve the record
                retrieved = db_writer.get_method_by_name(original_method.name)
                
                # Property 2: Content should match the most recent insert
                last_method = methods_to_insert[-1]
                assert retrieved is not None
                assert retrieved.name == last_method.name
                assert retrieved.description == last_method.description
                assert retrieved.parameters_json == last_method.parameters_json
                assert retrieved.return_type == last_method.return_type
                assert retrieved.module_path == last_method.module_path
                assert retrieved.function_name == last_method.function_name
                
            finally:
                # Clean up this test's data
                cursor.execute(
                    "DELETE FROM registered_methods WHERE name = %s;",
                    (original_method.name,)
                )
                conn.commit()
                cursor.close()
                db_writer.db_connection.return_connection(conn)
        
        # Run the property test
        property_test()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
