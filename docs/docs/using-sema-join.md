---
sidebar_position: 5
---

# Using Project SEMA-JOIN

Learn how to perform semantic table joins using the Project SEMA-JOIN interface.

**Prerequisites:** Complete [Environment Setup](./environment-setup), [Installation](./installation), and [Corpus Ingestion](./corpus-ingestion) before proceeding.

## Starting the Application

Start both the backend service and web interface:

```bash
./sema-join.sh run
```

The backend will run on port 8000 and the frontend on port 3000.

Access the web interface by opening your browser and navigating to:

```
http://localhost:3000
```

To start services individually:

```bash
# Start backend only
./sema-join.sh run backend

# Start frontend only
./sema-join.sh run frontend

# Start AI service
./sema-join.sh ai serve
```

## Uploading Tables

Project SEMA-JOIN requires two tables to perform a join: Table R and Table S.

### Table Format

Tables should be provided in JSON format with a specific structure. The data consists of a two-dimensional array where the first row contains column headers and subsequent rows contain the data values.

### Upload Methods

**File Upload**  
Click the upload button for Table R or Table S and select your JSON file.

![Upload Tables](/img/how_2_sema_join/upload_tables.png)

### Table Preview

After uploading, a preview of your table will appear. Verify that columns and data are displayed correctly.

![Preview Tables](/img/how_2_sema_join/preview_tables.png)

## Selecting Join Columns

After uploading both tables, specify which columns to use for joining.

### Manual Selection

Review the column headers and select the columns from each table that should be matched. For example, if Table R has a "country_name" column and Table S has a "country_code" column, select these as your join columns.

![Select Columns Manually](/img/how_2_sema_join/select_columns_manually.png)

### AI-Powered Suggestions

If the AI service is running, use the automatic column suggestion feature. This addresses an area identified in the original research as important future work: determining the joining columns without user input.

The AI analyzes both tables and recommends which columns to join based on column names, data patterns, and semantic relationships. It provides a confidence score and explanation. Review the suggestion and accept it or manually adjust your selection.

![AI Suggest Column for Bridge](/img/how_2_sema_join/ai_suggest_column_for_bridge.png)

## Creating the Bridge Table

The bridge table shows potential matches between values from your selected columns.

### Step 1: Choose Algorithm

Select one of two algorithms:

**CS-JP-LP**  
Uses column-level semantic compatibility scores with linear programming optimization to find the optimal solution. Provides the highest quality results (F-score) among all semantic join approaches. Best for smaller tables where maximum accuracy is critical.

**RS-JP**  
Simplified variant that uses row-level PMI scores for greedy matching. According to the research, RS-JP completes joins in under one second for all tested tasks. While F-score is a few percentage points behind CS-JP-LP, RS-JP is substantially better than traditional similarity-based join techniques, with quality improvements as high as 20 percentage points. Recommended as a reasonable alternative when CS-JP-LP becomes too expensive, or for larger tables requiring faster execution.

![Choose Algorithm](/img/how_2_sema_join/choose_algo_and_top_k.png)

### Step 2: Set Top K Matches

Choose how many candidate matches to show for each value:

- **K = 1**: Automatically uses the best match for each value
- **K > 1**: Shows multiple candidates, allowing you to manually select the correct matches

### Step 3: Create Bridge Table

Click "Create Bridge Table" to generate the matches. The system analyzes semantic relationships and calculates PMI scores for all potential value pairs.

### Step 4: Select Matches (if K > 1)

If you set K > 1, the bridge table will show multiple candidate matches for each value. Review the candidates and their PMI scores, then manually select which matches to use for the final join.

Higher PMI scores indicate stronger semantic relationships based on corpus co-occurrence patterns.

![Select Values for Bridge Table](/img/how_2_sema_join/select_values_for_bridge_table.png)

## Performing the Join

Once you have created your bridge table and selected the matches:

1. Click "Join Tables"
2. The system joins Table R and Table S using your bridge table mappings
3. The result shows combined data from both tables

## Viewing Results

The joined result table displays:

- All columns from both original tables
- Only rows where matches were found
- The relationships defined in your bridge table

Review the results to verify they meet your expectations.

![Join Results](/img/how_2_sema_join/join_results.png)


You now have a complete understanding of how to use Project SEMA-JOIN for semantic table joins. Experiment with different tables, algorithms, and features to find the best approach for your data integration needs.

