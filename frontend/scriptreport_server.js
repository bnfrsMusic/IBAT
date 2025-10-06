// PyExecJS compatible version - no require() statements
// This version returns data that Python will handle

function addReport(title, content, source) {
    const newReport = {
        title: title,
        content: content || "",
        source: source || null,
        timestamp: new Date().toISOString(),
        id: Date.now() + Math.random() // Unique ID
    };
    
    return newReport;
}

function createReportBatch(reportArray) {
    // Helper function to create multiple reports at once
    const reports = [];
    
    for (let i = 0; i < reportArray.length; i++) {
        const item = reportArray[i];
        reports.push(addReport(item.title, item.content, item.source));
    }
    
    return reports;
}