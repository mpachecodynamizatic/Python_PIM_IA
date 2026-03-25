export interface DatabaseOperationResult {
  [table: string]: number;  // table name -> count deleted/created
}
