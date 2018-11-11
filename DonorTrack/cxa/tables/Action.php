<?php
namespace CXA\TMS;
require_once('Table.php');
require_once($_SERVER['DOCUMENT_ROOT'].'/cxa/php/session.php');

interface Action
{
	public function run($data);
}

trait TableActionAuth
{
	protected function find_auth_level()
	{
		if (isset($this->table->config['data'][$this->auth_source]))
		{
			return (int)($this->table->config['data'][$this->auth_source]);
		}
		else if (isset($this->table->config['data']['table_auth']))
		{
			return (int)($this->table->config['data']['table_auth']);
		}
		else
		{
			return 4;
		}
	}
}

trait ColumnActionAuth
{
	protected function find_auth_level()
	{
		if (isset($this->table->config['columns'][$this->column_name][$this->auth_source]))
		{
			$this->auth_level = (int)($this->table->config['columns'][$this->column_name][$this->auth_source]);
		}
		else if (isset($this->table->config['data']['table_auth']))
		{
			$this->auth_level = (int)($this->table->config['data']['table_auth']);
		}
		else
		{
			$this->auth_level = 4;
		}
	}
}

abstract class BaseAction implements Action
{
	protected $table;
	protected $auth_level;
	protected $auth_source = '';
	
	function __construct(Table $table)
	{
		$this->table = $table;
		$this->auth_level = $this->find_auth_level();
	}
	
	abstract protected function find_auth_level();
	
	public function run($data)
	{
		if(!authorized($this->auth_level))
		{
			error_log('Failed access attempt at level '.$level.' by '.$_SESSION["userdata"]["username"].' with authorization level '.$_SESSION["userdata"]["authorization"].'!');
			http_response_code(403);
			echo('unauthorized');
			exit();
		}
	}
}

class GetAction extends BaseAction
{
	use TableActionAuth;
	
	protected $auth_source = 'get_auth';
	protected $query;
	
	function __construct(Table $table)
	{
		parent::__construct($table);
		
		$this->query = $this->build_query();
	}
	
	protected function build_query()
	{
		$columns = $this->table->get_columns();
		$query = "SELECT ";
		
		foreach ($columns as $column)
		{
			$column_name = $column->get_name();
			
			if ($column_name !== null)
			{
				$query .= "`".$column_name."`, ";
			}
		}
		
		$query = rtrim($query, ", ");
		$query .= " FROM `".$this->table->get_schema_name()."`;";
		
		return $query;
	}
	
	protected function query()
	{
		global $conn;
		
		$result = $conn->query($this->query);
		if (!$result)
		{
			error_log('Error #'.$conn->errno.' while running query '.$this->query);
			http_response_code(500);
			echo('database error');
			exit();
		}
		
		return $result;
	}
	
	protected function output($result)
	{
		$results = array();
		while ($row = ($result->fetch_assoc()))
		{
			$results[] = $row;
		}
		
		header("Content-Type: application/json");
		echo(json_encode($results));
		exit();
	}
	
	public function run($data)
	{
		parent::run($data);
		
		$result =  $this->query();
		$this->output($result);
	}
}

class GetUsers extends GetAction
{
	protected function output($result)
	{
		$results = array();
		while ($row = ($result->fetch_assoc()))
		{
			if ($row['userid'] == 777)
			{
				// Ignore guest user
				continue;
			}
			
			$results[] = $row;
		}
		
		header("Content-Type: application/json");
		echo(json_encode($results));
		exit();
	}
}

class SetAction extends BaseAction
{
	use TableActionAuth;
	
	protected $auth_source = 'set_auth';
	protected $statement;
	protected $bound_data = array();
	
	function __construct(Table $table)
	{
		parent::__construct($table);
	}
	
	protected function pre_validate($data_columns)
	{
		$columns = $this->table->get_columns();
		$final_columns = array();
		
		foreach ($columns as $column)
		{
			$column_name = $column->get_name();
			
			if ($column_name !== null)
			{
				if (isset($data_columns[$column_name]))
				{
					$final_columns[$column_name] = $column;
				}
				else if ($column->mandatory)
				{
					http_response_code(400);
					echo('missing column '.$column_name);
					exit();
				}
			}
		}
		
		return $final_columns;
	}
	
	protected function build_query($columns)
	{
		$query = "UPDATE `".$this->table->get_schema_name()."` SET ";
		
		foreach ($columns as $column)
		{
			$column_name = $column->get_name();
			
			if ($column_name !== null && $column_name != $this->table->get_primary_key())
			{
				$query .= "`".$column_name."`=?, ";
			}
		}
		
		$query = rtrim($query, ", ");
		$query .= " WHERE `".$this->table->get_primary_key()."`=? LIMIT 1;";
		
		return $query;
	}
	
	protected function setup_bindings($columns)
	{
		$bind_types = "";
		$params = array("");
		
		foreach ($columns as $column)
		{
			$column_name = $column->get_name();
			
			if ($column_name !== null && $column_name != $this->table->get_primary_key())
			{
				$bind_types .= $column->get_bind_type();
				
				$this->bound_data[$column_name] = null;
				$params[] = &$this->bound_data[$column_name];
			}
		}
		
		$bind_types .= $columns[$this->table->get_primary_key()]->get_bind_type();
		$this->bound_data[$this->table->get_primary_key()] = null;
		$params[] = &$this->bound_data[$this->table->get_primary_key()];
		$params[0] = $bind_types;
		
		return call_user_func_array(array($this->statement, 'bind_param'), $params);
	}
	
	protected function execute()
	{
		global $conn;
		
		if (!$this->statement->execute())
		{
			error_log('Error #'.$conn->errno.' while executing statement.');
			http_response_code(500);
			echo('database error');
			exit();
		}
		
		$result = $this->statement->get_result();
		if (!$result && $conn->errno)
		{
			error_log('Error #'.$conn->errno.' while retrieving statement result.');
			http_response_code(500);
			echo('database error');
			exit();
		}
		
		return $result;
	}
	
	public function run($data)
	{
		global $conn;
		parent::run($data);
		
		$columns = $this->pre_validate($data);
		$query = $this->build_query($columns);
		$this->statement = $conn->prepare($query);
		
		if (!$this->statement)
		{
			error_log('Error #'.$conn->errno.' while preparing query '.$this->query);
			http_response_code(500);
			echo('database error');
			exit();
		}
		
		if(!$this->setup_bindings($columns))
		{
			error_log('Error #'.$conn->errno.' while configuring statement bindings.');
			http_response_code(500);
			echo('database error');
			exit();
		}
		
		foreach ($columns as $column)
		{
			$column_name = $column->get_name();
			
			if ($column_name !== null)
			{
				$this->bound_data[$column_name] = $column->process($data[$column_name]);
			}
		}
		
		$this->execute();
		
		echo('ok');
		exit();
	}
}

class NewAction implements Action
{
	public function run($data)
	{
		
	}
}

class DelAction implements Action
{
	public function run($data)
	{
		
	}
}

class ApproveUserAction implements Action
{
	public function run($data)
	{
		
	}
}

class ResetPasswordAction implements Action
{
	public function run($data)
	{
		
	}
}

?>
