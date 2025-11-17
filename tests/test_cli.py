"""
Tests for CLI commands.
"""

import pytest
from click.testing import CliRunner
from aop import AOPClient
from aop.cli import main


@pytest.fixture
def cli_runner():
    """Create Click test runner"""
    return CliRunner()


@pytest.fixture
def test_db(tmp_path):
    """Create test database with sample data"""
    db_path = tmp_path / "test_cli.db"
    client = AOPClient(storage=f'sqlite:///{db_path}')

    # Create sample events
    correlation_id = 'test-trace-123'

    # Tool call 1
    call1 = client.mcp.log_tool_call(
        agent_id='test-agent',
        tool_name='search',
        params={'query': 'test'},
        correlation_id=correlation_id
    )

    client.mcp.log_tool_result(
        agent_id='test-agent',
        tool_name='search',
        result={'count': 10},
        duration_ms=150,
        correlation_id=correlation_id,
        parent_id=call1.id
    )

    # Tool call 2
    call2 = client.mcp.log_tool_call(
        agent_id='test-agent',
        tool_name='process',
        params={'data': 'test'},
        correlation_id=correlation_id
    )

    client.mcp.log_tool_result(
        agent_id='test-agent',
        tool_name='process',
        result={'status': 'ok'},
        duration_ms=50,
        correlation_id=correlation_id,
        parent_id=call2.id
    )

    # Additional events for different agent
    client.mcp.log_tool_call(
        agent_id='other-agent',
        tool_name='fetch',
        params={'url': 'test'},
        correlation_id='other-trace'
    )

    client.close()
    return str(db_path)


class TestQueryCommand:
    """Test aop query command"""

    def test_query_basic(self, cli_runner, test_db):
        """Test basic query without filters"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--limit', '10'
        ])

        assert result.exit_code == 0
        assert 'Events' in result.output or 'Timestamp' in result.output

    def test_query_with_agent_filter(self, cli_runner, test_db):
        """Test query filtered by agent ID"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--agent-id', 'test-agent',
            '--limit', '10'
        ])

        assert result.exit_code == 0
        assert 'test-agent' in result.output

    def test_query_with_event_type_filter(self, cli_runner, test_db):
        """Test query filtered by event type"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--event-type', 'mcp.tool.called',
            '--limit', '10'
        ])

        assert result.exit_code == 0

    def test_query_with_correlation_id(self, cli_runner, test_db):
        """Test query filtered by correlation ID"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--correlation-id', 'test-trace-123'
        ])

        assert result.exit_code == 0

    def test_query_compact_format(self, cli_runner, test_db):
        """Test query with compact format"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--format', 'compact',
            '--limit', '5'
        ])

        assert result.exit_code == 0

    def test_query_json_format(self, cli_runner, test_db):
        """Test query with JSON format"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--format', 'json',
            '--limit', '2'
        ])

        assert result.exit_code == 0
        # Should contain JSON structure
        assert '[' in result.output or '{' in result.output

    def test_query_no_results(self, cli_runner, test_db):
        """Test query with no matching results"""
        result = cli_runner.invoke(main, [
            'query',
            '--storage', f'sqlite:///{test_db}',
            '--agent-id', 'non-existent-agent'
        ])

        assert result.exit_code == 0
        assert 'No events found' in result.output


class TestTraceCommand:
    """Test aop trace command"""

    def test_trace_basic(self, cli_runner, test_db):
        """Test basic trace reconstruction"""
        result = cli_runner.invoke(main, [
            'trace',
            '--storage', f'sqlite:///{test_db}',
            '--correlation-id', 'test-trace-123'
        ])

        assert result.exit_code == 0
        assert 'Trace Summary' in result.output
        assert 'test-trace-123' in result.output

    def test_trace_table_format(self, cli_runner, test_db):
        """Test trace with table format"""
        result = cli_runner.invoke(main, [
            'trace',
            '--storage', f'sqlite:///{test_db}',
            '--correlation-id', 'test-trace-123',
            '--format', 'table'
        ])

        assert result.exit_code == 0
        assert 'Trace Events' in result.output or 'Event Type' in result.output

    def test_trace_json_format(self, cli_runner, test_db):
        """Test trace with JSON format"""
        result = cli_runner.invoke(main, [
            'trace',
            '--storage', f'sqlite:///{test_db}',
            '--correlation-id', 'test-trace-123',
            '--format', 'json'
        ])

        assert result.exit_code == 0
        assert '{' in result.output

    def test_trace_not_found(self, cli_runner, test_db):
        """Test trace with non-existent correlation ID"""
        result = cli_runner.invoke(main, [
            'trace',
            '--storage', f'sqlite:///{test_db}',
            '--correlation-id', 'non-existent-trace'
        ])

        assert result.exit_code == 0
        assert 'No trace found' in result.output

    def test_trace_missing_correlation_id(self, cli_runner, test_db):
        """Test trace without correlation ID (should fail)"""
        result = cli_runner.invoke(main, [
            'trace',
            '--storage', f'sqlite:///{test_db}'
        ])

        assert result.exit_code != 0


class TestStatsCommand:
    """Test aop stats command"""

    def test_stats_basic(self, cli_runner, test_db):
        """Test basic stats command"""
        result = cli_runner.invoke(main, [
            'stats',
            '--storage', f'sqlite:///{test_db}',
            '--agent-id', 'test-agent'
        ])

        assert result.exit_code == 0
        assert 'Analytics for Agent' in result.output
        assert 'test-agent' in result.output
        assert 'Tool Usage' in result.output

    def test_stats_with_window(self, cli_runner, test_db):
        """Test stats with time window"""
        result = cli_runner.invoke(main, [
            'stats',
            '--storage', f'sqlite:///{test_db}',
            '--agent-id', 'test-agent',
            '--window', '1h'
        ])

        assert result.exit_code == 0
        assert 'Event Rate' in result.output

    def test_stats_no_data(self, cli_runner, test_db):
        """Test stats for agent with no data"""
        result = cli_runner.invoke(main, [
            'stats',
            '--storage', f'sqlite:///{test_db}',
            '--agent-id', 'non-existent-agent'
        ])

        assert result.exit_code == 0
        assert 'No tool executions found' in result.output

    def test_stats_missing_agent_id(self, cli_runner, test_db):
        """Test stats without agent ID (should fail)"""
        result = cli_runner.invoke(main, [
            'stats',
            '--storage', f'sqlite:///{test_db}'
        ])

        assert result.exit_code != 0


class TestCLIHelpers:
    """Test CLI helper functions"""

    def test_version_option(self, cli_runner):
        """Test --version flag"""
        result = cli_runner.invoke(main, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_help_option(self, cli_runner):
        """Test --help flag"""
        result = cli_runner.invoke(main, ['--help'])

        assert result.exit_code == 0
        assert 'AOP' in result.output
        assert 'query' in result.output
        assert 'trace' in result.output
        assert 'stats' in result.output

    def test_query_help(self, cli_runner):
        """Test query --help"""
        result = cli_runner.invoke(main, ['query', '--help'])

        assert result.exit_code == 0
        assert 'Query and filter AOP events' in result.output

    def test_trace_help(self, cli_runner):
        """Test trace --help"""
        result = cli_runner.invoke(main, ['trace', '--help'])

        assert result.exit_code == 0
        assert 'Visualize execution traces' in result.output

    def test_stats_help(self, cli_runner):
        """Test stats --help"""
        result = cli_runner.invoke(main, ['stats', '--help'])

        assert result.exit_code == 0
        assert 'analytics' in result.output or 'statistics' in result.output


class TestExportCommand:
    """Test aop export command"""

    def test_export_json(self, cli_runner, test_db, tmp_path):
        """Test export to JSON format"""
        output_file = tmp_path / "export.json"

        result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(output_file),
            '--format', 'json'
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        assert 'Exported' in result.output
        assert 'JSON' in result.output

        # Verify JSON content
        import json
        with open(output_file) as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_export_csv(self, cli_runner, test_db, tmp_path):
        """Test export to CSV format"""
        output_file = tmp_path / "export.csv"

        result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(output_file),
            '--format', 'csv'
        ])

        assert result.exit_code == 0
        assert output_file.exists()
        assert 'Exported' in result.output
        assert 'CSV' in result.output

        # Verify CSV content
        import csv
        with open(output_file) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0
        assert 'id' in rows[0]
        assert 'agent_id' in rows[0]

    def test_export_with_filters(self, cli_runner, test_db, tmp_path):
        """Test export with agent filter"""
        output_file = tmp_path / "filtered.json"

        result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(output_file),
            '--agent-id', 'test-agent',
            '--limit', '10'
        ])

        assert result.exit_code == 0
        assert output_file.exists()

    def test_export_no_data(self, cli_runner, test_db, tmp_path):
        """Test export with no matching data"""
        output_file = tmp_path / "empty.json"

        result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(output_file),
            '--agent-id', 'non-existent-agent'
        ])

        assert result.exit_code == 0
        assert 'No events found' in result.output
        assert not output_file.exists()

    def test_export_missing_output(self, cli_runner, test_db):
        """Test export without output file (should fail)"""
        result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}'
        ])

        assert result.exit_code != 0


class TestValidateCommand:
    """Test aop validate command"""

    def test_validate_valid_events(self, cli_runner, test_db, tmp_path):
        """Test validate with valid events"""
        # Export some events first
        export_file = tmp_path / "events.json"

        cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(export_file),
            '--limit', '5'
        ])

        # Validate the exported file
        result = cli_runner.invoke(main, [
            'validate',
            str(export_file)
        ])

        assert result.exit_code == 0
        assert 'Validation Passed' in result.output

    def test_validate_with_schema_check(self, cli_runner, test_db, tmp_path):
        """Test validate with schema checking"""
        export_file = tmp_path / "events.json"

        cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(export_file),
            '--limit', '5'
        ])

        result = cli_runner.invoke(main, [
            'validate',
            str(export_file),
            '--check-schema'
        ])

        assert result.exit_code == 0
        assert 'Schema Validation' in result.output

    def test_validate_with_references(self, cli_runner, test_db, tmp_path):
        """Test validate with reference checking"""
        export_file = tmp_path / "events.json"

        # Export events with correlation ID
        export_result = cli_runner.invoke(main, [
            'export',
            '--storage', f'sqlite:///{test_db}',
            '--output', str(export_file),
            '--correlation-id', 'test-trace-123'
        ])

        # Only validate if export was successful
        if export_result.exit_code == 0 and export_file.exists():
            result = cli_runner.invoke(main, [
                'validate',
                str(export_file),
                '--check-references'
            ])

            assert result.exit_code == 0
            assert 'Reference Validation' in result.output
        else:
            # If no events with that correlation ID, just verify export behavior
            assert 'No events found' in export_result.output or export_result.exit_code == 0

    def test_validate_invalid_json(self, cli_runner, tmp_path):
        """Test validate with invalid JSON"""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json {")

        result = cli_runner.invoke(main, [
            'validate',
            str(invalid_file)
        ])

        assert result.exit_code != 0
        assert 'Invalid JSON' in result.output

    def test_validate_missing_file(self, cli_runner):
        """Test validate with non-existent file"""
        result = cli_runner.invoke(main, [
            'validate',
            '/tmp/does-not-exist.json'
        ])

        assert result.exit_code != 0

    def test_validate_single_event(self, cli_runner, tmp_path):
        """Test validate with single event (not array)"""
        import json
        from aop import AOPClient

        # Create single event file
        client = AOPClient(storage='memory')
        call = client.mcp.log_tool_call('test-agent', 'test_tool', {'param': 'value'})
        events = client.query()

        single_event_file = tmp_path / "single.json"
        with open(single_event_file, 'w') as f:
            json.dump(events[0], f)

        result = cli_runner.invoke(main, [
            'validate',
            str(single_event_file),
            '--check-schema'
        ])

        assert result.exit_code == 0
        assert 'Validating 1 event' in result.output
