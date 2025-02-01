package com.twitch.atlas;

import java.awt.Color;
import java.awt.Font;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.gephi.appearance.api.AppearanceController;
import org.gephi.appearance.api.AppearanceModel;
import org.gephi.appearance.api.Function;
import org.gephi.appearance.api.Partition;
import org.gephi.appearance.api.PartitionFunction;
import org.gephi.appearance.plugin.PartitionElementColorTransformer;
import org.gephi.appearance.plugin.RankingLabelSizeTransformer;
import org.gephi.appearance.plugin.RankingNodeSizeTransformer;
import org.gephi.appearance.plugin.palette.Palette;
import org.gephi.appearance.plugin.palette.PaletteManager;
import org.gephi.graph.api.Column;
import org.gephi.graph.api.Edge;
import org.gephi.graph.api.Graph;
import org.gephi.graph.api.GraphController;
import org.gephi.graph.api.GraphModel;
import org.gephi.graph.api.UndirectedGraph;
import org.gephi.io.database.drivers.SQLiteDriver;
import org.gephi.io.exporter.api.ExportController;
import org.gephi.io.exporter.preview.PNGExporter;
import org.gephi.io.exporter.spi.GraphExporter;
import org.gephi.io.importer.api.Container;
import org.gephi.io.importer.api.EdgeDirectionDefault;
import org.gephi.io.importer.api.ImportController;
import org.gephi.io.importer.plugin.database.EdgeListDatabaseImpl;
import org.gephi.io.importer.plugin.database.ImporterEdgeList;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.layout.plugin.forceAtlas2.ForceAtlas2;
import org.gephi.layout.spi.Layout;
import org.gephi.preview.api.PreviewController;
import org.gephi.preview.api.PreviewModel;
import org.gephi.preview.api.PreviewProperty;
import org.gephi.preview.types.DependantColor;
import org.gephi.preview.types.DependantOriginalColor;
import org.gephi.project.api.ProjectController;
import org.gephi.project.api.Workspace;
import org.gephi.statistics.plugin.Modularity;
import org.openide.util.Lookup;

// import uk.ac.ox.oii.jsonexporter.JSONExporter;
public class App {

    public static void main(String[] args) {
        // GatewayServer gatewayServer = new GatewayServer(new App());
        // gatewayServer.start();
        // System.out.println("Gateway Server Started");
        System.setProperty("jdbc.drivers", "org.sqlite.JDBC");
        System.setProperty("org.netbeans.core.startup.preferences.PreferencesProviderImpl", "false");
        Run(0);
    }

    public static void Run(int batch_id) {
        System.out.println("Atlas Generation Started");
        // Init a project - and therefore a workspace

        int numImages = 10;
        for (int i = 0; i < numImages; i++) {
            ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
            pc.newProject();
            Workspace workspace = pc.getCurrentWorkspace();

            ImportController importController = Lookup.getDefault().lookup(ImportController.class);

            GraphModel graphModel = LoadGraph(importController, workspace, batch_id);

            LayoutGraph(graphModel);
            SetGraphPreview();

            UndirectedGraph graph = graphModel.getUndirectedGraph();
            // ExportGexf(graph, "../../Website/webdata.json");
            ExportGraph(graph, i);

        }
        System.exit(0);
    }

    public static void SetGraphPreview() {
        //Preview
        PreviewModel model = Lookup.getDefault().lookup(PreviewController.class).getModel();
        //Node Label Properties
        model.getProperties().putValue(PreviewProperty.SHOW_NODE_LABELS, Boolean.TRUE);
        model.getProperties().putValue(PreviewProperty.NODE_LABEL_PROPORTIONAL_SIZE, Boolean.TRUE);
        model.getProperties().putValue(PreviewProperty.NODE_LABEL_FONT, new Font("Arial", Font.PLAIN, 18));

        model.getProperties().putValue(PreviewProperty.NODE_LABEL_COLOR, new DependantOriginalColor(Color.WHITE));

        model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_SIZE, 4.0f);
        model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_OPACITY, 40);
        model.getProperties().putValue(PreviewProperty.NODE_LABEL_OUTLINE_COLOR, new DependantColor(Color.BLACK));

        //Edge Properties
        model.getProperties().putValue(PreviewProperty.SHOW_EDGES, Boolean.TRUE);
        model.getProperties().putValue(PreviewProperty.EDGE_THICKNESS, 10.0);
        model.getProperties().putValue(PreviewProperty.EDGE_RESCALE_WEIGHT, Boolean.TRUE);
        model.getProperties().putValue(PreviewProperty.EDGE_RESCALE_WEIGHT_MIN, .1);
        model.getProperties().putValue(PreviewProperty.EDGE_OPACITY, 100);

        //Image Properties
        model.getProperties().putValue(PreviewProperty.BACKGROUND_COLOR, Color.BLACK);
    }

    public static void LayoutGraph(GraphModel graphModel) {
        Graph undirectedGraph = graphModel.getUndirectedGraph();

        System.out.println("Edge removal");
        int edgeWeightLowerBound = 1000;
        List<Edge> edgesToRemove = new ArrayList<>();
        for (Edge e : undirectedGraph.getEdges().toArray()) {
            if ((double) e.getAttribute("Weight") < edgeWeightLowerBound) {
                edgesToRemove.add(e);
            }
        }
        if (!edgesToRemove.isEmpty()) {
            undirectedGraph.removeAllEdges(edgesToRemove);
        }

        System.out.println("before node removal graph contains node count: ");
        System.out.println(undirectedGraph.getNodeCount());

        // Comment out node removal logic to ensure no nodes are removed
        // int nodeCountLowerBound = 1;
        // List<Node> nodesToRemove = new ArrayList<>();
        // for (Node n : undirectedGraph.getNodes().toArray()) {
        //     Object count = n.getAttribute("count");
        //     if (count == null) {
        //         nodesToRemove.add(n);
        //     } else {
        //         long countValue;
        //         if (count instanceof Integer) {
        //             countValue = ((Integer) count).longValue();
        //         } else if (count instanceof Long) {
        //             countValue = (Long) count;
        //         } else {
        //             continue;
        //         }
        //         if (countValue < nodeCountLowerBound) {
        //             nodesToRemove.add(n);
        //         }
        //     }
        // }
        // if (!nodesToRemove.isEmpty()) {
        //     undirectedGraph.removeAllNodes(nodesToRemove);
        // }
        System.out.println("After node removal graph contains node count: ");
        System.out.println(undirectedGraph.getNodeCount());

        // Disable or bypass filtering step
        // Remove degree filter by commenting out the following lines
        // FilterController filterController = Lookup.getDefault().lookup(FilterController.class);
        // DegreeRangeFilter degreeFilter = new DegreeRangeFilter();
        // degreeFilter.setRange(new Range(1, Integer.MAX_VALUE)); // Remove nodes with degree < 10
        // Query query = filterController.createQuery(degreeFilter);
        // GraphView view = filterController.filter(query);
        // graphModel.setVisibleView(view); // Set the filter result as the visible view
        // No filtering, just keep the entire graph visible
        // Optionally, set the entire graph as visible again if filtering is applied
        // graphModel.setVisibleView(graphModel.getGraphView());
        Modularity modularity = new Modularity();
        modularity.setResolution(0.4);
        modularity.setUseWeight(true);
        modularity.execute(graphModel);

        // Partition with 'modularity_class', just created by Modularity algorithm
        AppearanceController appearanceController = Lookup.getDefault().lookup(AppearanceController.class);
        AppearanceModel appearanceModel = appearanceController.getModel();

        Column modColumn = graphModel.getNodeTable().getColumn(Modularity.MODULARITY_CLASS);

        Function func2 = appearanceModel.getNodeFunction(modColumn, PartitionElementColorTransformer.class);
        Partition partition2 = ((PartitionFunction) func2).getPartition();

        Palette palette2 = PaletteManager.getInstance().randomPalette(partition2.size(undirectedGraph));

        int i = 0;
        for (Object o : partition2.getValues(undirectedGraph)) {
            partition2.setColor(o, palette2.getColors()[i]);
            i++;
        }
        appearanceController.transform(func2);

        Column rankingCol = graphModel.getNodeTable().getColumn("count");

        if (rankingCol == null) {
            throw new RuntimeException("Column 'count' does not exist in GraphModel. Check if it's being imported correctly.");
        }

        Function rankingNodeSize = appearanceModel.getNodeFunction(rankingCol, RankingNodeSizeTransformer.class);
        Function rankingLabelSize = appearanceModel.getNodeFunction(rankingCol, RankingLabelSizeTransformer.class);

        RankingNodeSizeTransformer rankingNodeSizeTransformer = rankingNodeSize.getTransformer();
        RankingLabelSizeTransformer rankingLabelSizeTransformer = rankingLabelSize.getTransformer();

        rankingNodeSizeTransformer.setMinSize(10f);
        rankingNodeSizeTransformer.setMaxSize(40f);

        rankingLabelSizeTransformer.setMinSize(0.3f);
        rankingLabelSizeTransformer.setMaxSize(0.4f);

        appearanceController.transform(rankingNodeSize);
        appearanceController.transform(rankingLabelSize);

        // No layout changes needed for this example, but here you can continue with your layout logic
        ForceAtlas2 forceAtlasStep = new ForceAtlas2(null);
        forceAtlasStep.resetPropertiesValues();
        forceAtlasStep.setGraphModel(graphModel);
        forceAtlasStep.setAdjustSizes(true);
        forceAtlasStep.setLinLogMode(true);
        forceAtlasStep.setOutboundAttractionDistribution(false);
        forceAtlasStep.setScalingRatio(5d);
        forceAtlasStep.setGravity(3d);
        forceAtlasStep.setEdgeWeightInfluence(0.45d);

        // RUN FIRST PHASE
        Layout firstAlgo = forceAtlasStep;
        int firstAlgoSteps = 750;

        firstAlgo.initAlgo();

        System.out.println("FIRST PHASE EXECUTION");
        for (int k = 0; k < firstAlgoSteps; k++) {
            firstAlgo.goAlgo();
        }

        // CHANGE PARAMETERS AND RUN SECOND PHASE
        forceAtlasStep.setScalingRatio(1.5d);
        forceAtlasStep.setLinLogMode(false);
        forceAtlasStep.setEdgeWeightInfluence(0.28d);
        int secondAlgoSteps = 350;

        System.out.println("SECOND PHASE EXECUTION");
        for (int k = 0; k < secondAlgoSteps; k++) {
            firstAlgo.goAlgo();
        }

        // CHANGE PARAMETERS AND RUN THIRD PHASE
        forceAtlasStep.setScalingRatio(1.6d);
        forceAtlasStep.setLinLogMode(true);
        forceAtlasStep.setEdgeWeightInfluence(0.45d);
        int thirdAlgoSteps = 1100;

        System.out.println("THIRD PHASE EXECUTION");
        for (int k = 0; k < thirdAlgoSteps; k++) {
            firstAlgo.goAlgo();
        }

        System.out.println("ENDING LAYOUT EXECUTION");
    }

    public static GraphModel LoadGraph(ImportController importController, Workspace workspace, int batch_id) {
        System.out.println("STARTING LOAD GRAPH");

        // Define database path once
        String dbPath = "jdbc:sqlite:C:/Users/curtr/Documents/DB/twitch.db";

        // Load Gephi from RDBMS
        // Get controllers and models
        GraphModel graphModel = Lookup.getDefault().lookup(GraphController.class).getGraphModel();

        File file = new File("C:/Users/curtr/Documents/DB/twitch.db");

        // Import database into Gephi
        EdgeListDatabaseImpl db = new EdgeListDatabaseImpl();
        db.setHost(file.getAbsolutePath());
        db.setDBName("");
        db.setSQLDriver(new SQLiteDriver());

        // Debugging check
        if (db.getSQLDriver() == null) {
            throw new IllegalStateException("SQLite driver is not properly set in EdgeListDatabaseImpl.");
        }

        // db.setDBName("C:/Users/curtr/Documents/DB/twitch.db");
        db.setNodeQuery("SELECT c.url_name as id, c.url_name as label, c.view_minutes as count from channels c");
        db.setEdgeQuery("SELECT source, target, weight FROM channel_overlaps where batch_id=" + batch_id);

        System.out.println("Gephi DB Driver: " + db.getSQLDriver().getClass().getName());
        System.out.println("Database Path: " + dbPath);
        // System.out.println("Node Query: " + db.getNodeQuery());
        // System.out.println("Edge Query: " + db.getEdgeQuery());

        System.out.println("IMPORTING DATABASE");
        ImporterEdgeList edgeListImporter = new ImporterEdgeList();
        Container container = importController.importDatabase(db, edgeListImporter);
        container.getLoader().setEdgeDefault(EdgeDirectionDefault.UNDIRECTED);   // Force UNDIRECTED

        System.out.println("PROCESSING DATABASE");
        // Append imported data to GraphAPI
        importController.process(container, new DefaultProcessor(), workspace);

        System.out.println("ENDING LOAD GRAPH");
        return graphModel;
    }

    public static void ExportGraph(Graph graph, int imageNum) {
        // ExportController ec = Lookup.getDefault().lookup(ExportController.class);
        // PNGExporter exporter = (PNGExporter) ec.getExporter("png");
        // ByteArrayOutputStream baos = new ByteArrayOutputStream();
        // ec.exportStream(baos, exporter);
        // byte[] png = baos.toByteArray();
        // BufferedImage final_img = ImageIO.read(new ByteArrayInputStream(png));
        // File output_file = new File("NEW2.png");
        // ImageIO.write(final_img, "png", output_file);
        // return;
        //Export full graph
        ExportController ec = Lookup.getDefault().lookup(ExportController.class);
        //Export only visible graph
        PNGExporter exporter = (PNGExporter) ec.getExporter("png"); //Get GEXF exporter
        // exporter.setExportVisible(true); //Only exports the visible (filtered) graph

        //Set png options
        exporter.setHeight(4500);
        exporter.setWidth(4500);

        try {
            ec.exportFile(new File("./Images/GeneratedAtlas" + String.valueOf(imageNum) + ".png"), exporter);
        } catch (IOException ex) {
            ex.printStackTrace();
        }

        // Export GEXF
        try {
            GraphExporter graphExporter = (GraphExporter) ec.getExporter("gexf"); // Get GEXF exporter
            graphExporter.setExportVisible(true); // Export only visible graph
            graphExporter.setWorkspace(Lookup.getDefault().lookup(ProjectController.class).getCurrentWorkspace()); // Set the workspace to ensure the correct graph view is exported

            // Export the graph as a GEXF file
            ec.exportFile(new File("./Images/GeneratedAtlas" + String.valueOf(imageNum) + ".gexf"), graphExporter);
        } catch (IOException ex) {
            ex.printStackTrace();
        }

        System.out.println("ENDING");
    }

    public static void ExportGexf(Graph graph, String filename) {
        // ExportController ec = Lookup.getDefault().lookup(ExportController.class);
        // JSONExporter exporter = new JSONExporter();
        // // exporter.setExportVisible(true); //Only exports the visible (filtered) graph

        // try {
        //     ec.exportFile(new File(filename), exporter);
        // } catch (IOException ex) {
        //     ex.printStackTrace();
        // }
        // System.out.println("ENDING");
    }
}
