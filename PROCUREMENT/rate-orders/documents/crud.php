<?php

$folder_parts = array_values(array_filter(explode('/', $_SERVER['PHP_SELF'] ?? '')));
$folder_name = count($folder_parts) >= 2 ? $folder_parts[count($folder_parts) - 2] : 'esg_compliance_register';

$table = "esg_records";
$documents_table = "esg_record_documents";

if (!isset($pdo)) { require __DIR__ . '/../../config/dbconfig.php'; }
require_once __DIR__ . '/function.php';

$config = esg_compliance_register_config();
esg_compliance_register_bootstrap();
$action = $_POST['action'] ?? '';
$date = date('Y-m-d H:i:s');
$user_id = $_SESSION['sess_user_id'] ?? ($_SESSION['user_id'] ?? '');
$user_name = $_SESSION['user_name'] ?? ($_SESSION['sess_user_name'] ?? '');
$action_obj = (object)["status" => 0, "data" => "", "error" => "Action Not Performed"];

switch ($action) {
    case 'createupdate':
        $unique_id = trim($_POST['unique_id'] ?? '');
        $error = esg_compliance_register_validate_request($unique_id);
        if ($error !== '') {
            echo json_encode(['status' => 0, 'msg' => 'error', 'error' => $error]);
            break;
        }

        $master = esg_compliance_register_load_master($unique_id);
        if (empty($master)) {
            $unique_id = $unique_id ?: unique_id('esg');
            $recordNumber = esg_compliance_register_record_number(trim($_POST['company_id'] ?? ''));
            $masterColumns = esg_compliance_register_collect_master_columns($unique_id, $recordNumber, $user_id, $date);
            $action_obj = $pdo->insert(ESG_COMPLIANCE_MASTER_TABLE, $masterColumns);
            $msg = 'create';
            $masterId = $action_obj->status ? (int) $action_obj->data : 0;
        } else {
            $action_obj = (object) ['status' => 1, 'data' => $master['id'], 'error' => '', 'sql' => ''];
            $msg = 'update';
            $masterId = (int) $master['id'];
        }

        if ($action_obj->status && $masterId > 0) {
            $historyRowsJson = trim($_POST['history_rows_json'] ?? '');
            $historyRows = ($historyRowsJson !== '' && $historyRowsJson !== '[]')
                ? json_decode($historyRowsJson, true)
                : null;

            if (!empty($historyRows) && is_array($historyRows)) {
                foreach ($historyRows as $hrow) {
                    $notifyDays = max(0, (int) ($hrow['notify_days'] ?? 0));
                    $hCols = [
                        'unique_id'          => unique_id('hist'),
                        'compliance_id'      => $masterId,
                        'issue_date'         => $hrow['issue_date'] ?? null,
                        'expiry_date'        => ($hrow['expiry_date'] ?? '') !== '' ? $hrow['expiry_date'] : null,
                        'notify_days'        => $notifyDays,
                        'status'             => ($hrow['status_code'] ?? '') ?: 'active',
                        'responsible_person' => $hrow['owner_name'] ?? null,
                        'reference_number'   => $hrow['reference_number'] ?? null,
                        'document_path'      => null,
                        'remarks'            => $hrow['remarks'] ?? null,
                        'is_active'          => 1,
                        'is_delete'          => 0,
                        'created_at'         => $date,
                        'updated_at'         => $date,
                        'created'            => $date,
                        'updated'            => $date,
                        'created_user_id'    => $user_id,
                        'updated_user_id'    => $user_id,
                    ];
                    $action_obj = $pdo->insert(ESG_COMPLIANCE_HISTORY_TABLE, $hCols);
                    if (!$action_obj->status) break;
                }
            } else {
                $historyColumns = esg_compliance_register_collect_history_columns($masterId, $unique_id, $user_id, $date);
                $action_obj = $pdo->insert(ESG_COMPLIANCE_HISTORY_TABLE, $historyColumns);
            }
        }

        echo json_encode([
            'status' => $action_obj->status,
            'msg' => $msg,
            'data' => ['unique_id' => $unique_id],
            'error' => $action_obj->error,
            'sql' => $action_obj->sql
        ]);
        break;

    case 'datatable':
        $search = trim($_POST['search']['value'] ?? '');
        $length = $_POST['length'] ?? 10;
        $start = $_POST['start'] ?? 0;
        $draw = $_POST['draw'] ?? 1;
        $limit = $length === '-1' ? '' : $length;
        $columns = [
            '@a:=@a+1 AS s_no',
            'cm.record_number',
            'ch.reference_number',
            'cm.compliance_type_id',
            'ch.issue_date',
            'ch.expiry_date',
            'ch.status AS status_code',
            'cm.company_id',
            'cm.project_id',
            'ch.responsible_person AS owner_name',
            'cm.unique_id',
        ];
        $table_details = [
            ESG_COMPLIANCE_MASTER_TABLE . ' cm
                LEFT JOIN ' . ESG_COMPLIANCE_HISTORY_TABLE . ' ch ON ch.id = (
                    SELECT ch2.id
                    FROM ' . ESG_COMPLIANCE_HISTORY_TABLE . ' ch2
                    WHERE ch2.compliance_id = cm.id
                        AND ch2.is_delete = 0
                    ORDER BY ch2.id DESC
                    LIMIT 1
                ), (SELECT @a:= ' . (int) $start . ') AS a',
            $columns
        ];
        $where = 'cm.is_delete = 0';

        foreach (['company_id', 'project_id', 'category', 'entry_date', 'status_code', 'compliance_type_id'] as $filter) {
            if (!empty($_POST[$filter])) {
                if ($filter === 'entry_date') {
                    $column = 'ch.issue_date';
                } elseif ($filter === 'status_code') {
                    $column = 'ch.status';
                } elseif (in_array($filter, ['company_id', 'project_id', 'compliance_type_id'], true)) {
                    $column = 'cm.' . $filter;
                } else {
                    continue;
                }
                $where .= ' AND ' . $column . ' = "' . addslashes(trim($_POST[$filter])) . '"';
            }
        }

        if ($search !== '') {
            $search_safe = addslashes($search);
            $where .= ' AND (cm.record_number LIKE "%' . $search_safe . '%" OR ch.reference_number LIKE "%' . $search_safe . '%")';
        }

        $order_column = $_POST['order'][0]['column'] ?? 0;
        $order_dir = $_POST['order'][0]['dir'] ?? 'desc';
        $order_by = datatable_sorting($order_column, $order_dir, $columns);
        $result = $pdo->select($table_details, $where, $limit, $start, $order_by, 'SQL_CALC_FOUND_ROWS');
        $total_records = total_records();
        $data = [];

        if ($result->status) {
            $rows = $result->data;
            if (isset($rows['s_no'])) {
                $rows = [$rows];
            }
            foreach ($rows as $row) {
                $rowData = [$row['s_no']];
                foreach ($config['list_columns'] as $column) {
                    $rowData[] = esg_compliance_register_datatable_cell($row, $column);
                }
                $renewalBtn = '<a data-no-block href="index.php?file=' . $folder_name . '/update&unique_id=' . htmlspecialchars($row['unique_id']) . '" class="btn btn-sm btn-outline-primary ms-1" title="Add Renewal">Add Renewal</a>';
                $rowData[] = btn_views_icon($folder_name, $row['unique_id'], 'ESG') . $renewalBtn . btn_print($folder_name, $row['unique_id'], 'print', '', '', 'Print') . btn_delete($folder_name, $row['unique_id']);
                $data[] = $rowData;
            }
        }

        echo json_encode(['draw' => (int) $draw, 'recordsTotal' => (int) $total_records, 'recordsFiltered' => (int) $total_records, 'data' => $data, 'testing' => $result->sql ?? '']);
        break;

    case 'fetch':
        $unique_id = $_POST['unique_id'] ?? '';
        $record = esg_compliance_register_load_record($unique_id);
        $history = !empty($record['id']) ? esg_compliance_register_load_history($record['id']) : [];
        echo json_encode(['status' => !empty($record) ? 1 : 0, 'data' => $record, 'history' => $history, 'msg' => !empty($record) ? 'fetch' : 'not_found']);
        break;

    case 'history_add':
        $masterUniqueId = trim($_POST['master_unique_id'] ?? '');
        if ($masterUniqueId === '') {
            echo json_encode(['status' => 0, 'error' => 'Master record ID is required.']);
            break;
        }
        $master = esg_compliance_register_load_master($masterUniqueId);
        if (empty($master)) {
            echo json_encode(['status' => 0, 'error' => 'Master record not found.']);
            break;
        }
        $issueDate = esg_compliance_register_post_value('issue_date');
        if ($issueDate === null) {
            echo json_encode(['status' => 0, 'error' => 'Issue date is required.']);
            break;
        }
        $expiryDate = esg_compliance_register_post_value('expiry_date');
        if ($expiryDate !== null && strtotime($expiryDate) <= strtotime($issueDate)) {
            echo json_encode(['status' => 0, 'error' => 'Expiry date must be after issue date.']);
            break;
        }
        $historyColumns = esg_compliance_register_collect_history_columns((int)$master['id'], $masterUniqueId, $user_id, $date);
        $action_obj = $pdo->insert(ESG_COMPLIANCE_HISTORY_TABLE, $historyColumns);
        $newId = $action_obj->status ? (int)$action_obj->data : 0;
        $newRow = [];
        if ($newId > 0) {
            $fetchResult = $pdo->select([ESG_COMPLIANCE_HISTORY_TABLE, ['*']], ['id' => $newId]);
            if ($fetchResult->status && !empty($fetchResult->data)) {
                $newRow = $fetchResult->data[0] ?? $fetchResult->data;
            }
        }
        echo json_encode(['status' => $action_obj->status, 'msg' => 'history_add', 'data' => $newRow, 'error' => $action_obj->error]);
        break;

    case 'history_update':
        $historyId = (int)($_POST['history_id'] ?? 0);
        if ($historyId <= 0) {
            echo json_encode(['status' => 0, 'error' => 'History row ID is required.']);
            break;
        }
        $fetchExisting = $pdo->select([ESG_COMPLIANCE_HISTORY_TABLE, ['*']], ['id' => $historyId, 'is_delete' => 0]);
        if (!$fetchExisting->status || empty($fetchExisting->data)) {
            echo json_encode(['status' => 0, 'error' => 'History row not found.']);
            break;
        }
        $existing = $fetchExisting->data[0] ?? $fetchExisting->data;
        $masterUniqueId = trim($_POST['master_unique_id'] ?? '');
        $issueDate = esg_compliance_register_post_value('issue_date');
        if ($issueDate === null) {
            echo json_encode(['status' => 0, 'error' => 'Issue date is required.']);
            break;
        }
        $expiryDate = esg_compliance_register_post_value('expiry_date');
        if ($expiryDate !== null && strtotime($expiryDate) <= strtotime($issueDate)) {
            echo json_encode(['status' => 0, 'error' => 'Expiry date must be after issue date.']);
            break;
        }

        /* CHANGED: Handle multiple file uploads.
           New files are merged with existing document_path JSON array
           so previously uploaded files are preserved. */
        $documentPath = $existing['document_path'] ?? null;
        $filesArray = $_FILES['compliance_document_upload'] ?? null;
        if (!empty($filesArray) && !empty($filesArray['name'][0])) {
            $uploadRef = $masterUniqueId ?: ($existing['unique_id'] ?? '');
            $newStored = esg_compliance_register_store_documents($filesArray, $uploadRef);
            if (!empty($newStored)) {
                /* Decode existing docs (supports both JSON array and plain path string) */
                $existingDocs = [];
                if (!empty($documentPath)) {
                    $decoded = json_decode($documentPath, true);
                    if (is_array($decoded)) {
                        foreach ($decoded as $d) {
                            if (is_array($d) && !empty($d['path'])) {
                                $existingDocs[] = $d;
                            } elseif (is_string($d) && $d !== '') {
                                $existingDocs[] = ['name' => basename($d), 'path' => $d];
                            }
                        }
                    } elseif (is_string($documentPath) && $documentPath !== '') {
                        /* Legacy plain path string — treat as single entry */
                        $existingDocs[] = ['name' => basename($documentPath), 'path' => $documentPath];
                    }
                }
                $documentPath = json_encode(array_merge($existingDocs, $newStored));
            }
        }

        $updateColumns = [
            'issue_date'         => $issueDate,
            'expiry_date'        => $expiryDate,
            'notify_days'        => max(0, (int) (esg_compliance_register_post_value('notify_days') ?? 0)),
            'status'             => esg_compliance_register_post_value('status_code') ?: 'active',
            'responsible_person' => esg_compliance_register_post_value('owner_name'),
            'reference_number'   => esg_compliance_register_post_value('reference_number'),
            'document_path'      => $documentPath,
            'remarks'            => esg_compliance_register_post_value('remarks'),
            'updated_at'         => $date,
            'updated'            => $date,
            'updated_user_id'    => $user_id,
        ];
        $action_obj = $pdo->update(ESG_COMPLIANCE_HISTORY_TABLE, $updateColumns, ['id' => $historyId]);
        $updatedRow = [];
        if ($action_obj->status) {
            $fetchUpdated = $pdo->select([ESG_COMPLIANCE_HISTORY_TABLE, ['*']], ['id' => $historyId]);
            if ($fetchUpdated->status && !empty($fetchUpdated->data)) {
                $updatedRow = $fetchUpdated->data[0] ?? $fetchUpdated->data;
            }
        }
        echo json_encode(['status' => $action_obj->status, 'msg' => 'history_update', 'data' => $updatedRow, 'error' => $action_obj->error]);
        break;

    case 'history_delete':
        $historyId = (int)($_POST['history_id'] ?? 0);
        if ($historyId <= 0) {
            echo json_encode(['status' => 0, 'error' => 'History row ID is required.']);
            break;
        }
        $action_obj = $pdo->update(ESG_COMPLIANCE_HISTORY_TABLE, ['is_delete' => 1, 'updated_at' => $date, 'updated' => $date, 'updated_user_id' => $user_id], ['id' => $historyId]);
        echo json_encode(['status' => $action_obj->status, 'msg' => 'history_delete', 'error' => $action_obj->error]);
        break;

    case 'delete':
        $unique_id = $_POST['unique_id'] ?? '';
        $action_obj = $pdo->update(ESG_COMPLIANCE_MASTER_TABLE, ['is_delete' => 1, 'updated' => $date, 'updated_at' => $date, 'updated_user_id' => $user_id], ['unique_id' => $unique_id]);
        echo json_encode(['status' => $action_obj->status, 'msg' => $action_obj->status ? 'delete' : 'error', 'error' => $action_obj->error, 'sql' => $action_obj->sql]);
        break;


    // Thara
    case 'project_name':
        $company_id = $_POST['company_id'] ?? '';
        $project_options = esg_compliance_register_project_options($company_id);
        echo esg_compliance_register_select_options($project_options, 'Select Project');
        break;


    default:
        echo json_encode(['status' => 0, 'msg' => 'invalid_action']);
        break;
}