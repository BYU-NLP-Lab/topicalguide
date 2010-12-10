/**
 * The Topic Browser
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topic Browser is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topic Browser is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
 * for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topic Browser, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */
package edu.byu.nlp.topicvis;

import java.awt.Color;
import java.io.File;
import java.io.IOException;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;

import org.gephi.data.attributes.api.AttributeColumn;
import org.gephi.data.attributes.api.AttributeController;
import org.gephi.data.attributes.api.AttributeModel;
import org.gephi.filters.api.FilterController;
import org.gephi.graph.api.GraphController;
import org.gephi.graph.api.GraphModel;
import org.gephi.graph.api.GraphView;
import org.gephi.io.exporter.api.ExportController;
import org.gephi.io.generator.spi.Generator;
import org.gephi.io.importer.api.Container;
import org.gephi.io.importer.api.ContainerFactory;
import org.gephi.io.importer.api.ImportController;
import org.gephi.io.importer.api.Report;
import org.gephi.io.processor.plugin.DefaultProcessor;
import org.gephi.layout.plugin.AutoLayout;
import org.gephi.layout.plugin.force.StepDisplacement;
import org.gephi.layout.plugin.force.yifanHu.YifanHuLayout;
import org.gephi.layout.plugin.forceAtlas.ForceAtlasLayout;
import org.gephi.preview.api.PreviewController;
import org.gephi.preview.api.PreviewModel;
import org.gephi.project.api.ProjectController;
import org.gephi.project.api.Workspace;
import org.gephi.ranking.api.ColorTransformer;
import org.gephi.ranking.api.NodeRanking;
import org.gephi.ranking.api.RankingController;
import org.gephi.ranking.api.SizeTransformer;
import org.gephi.statistics.plugin.GraphDistance;
import org.openide.util.Lookup;

import edu.byu.nlp.topicvis.DistanceFilterBuilder.DistanceFilter;

public class TopicMapGraphBuilder {
	private final YambaDatabase db;
	private final String baseUrl;
	private final String datasetName;
	private final String analysisName;
	private final String topicNameScheme;
	private final Bijection<String> topicNameNumIdx;

	public TopicMapGraphBuilder(String yambaFilename, String baseUrl, String datasetName, String analysisName, String topicNameScheme) {
		this(new YambaDatabase(yambaFilename), baseUrl, datasetName, analysisName, topicNameScheme);
	}

	public TopicMapGraphBuilder(YambaDatabase db, String baseUrl, String datasetName, String analysisName, String topicNameScheme) {
		this(db, topicNameNumIdx(db, datasetName, analysisName, topicNameScheme), baseUrl, datasetName, analysisName, topicNameScheme);
	}

	public TopicMapGraphBuilder(YambaDatabase db, Bijection<String> topicNameNumIdx, String baseUrl, String datasetName, String analysisName, String topicNameScheme) {
		this.db = db;
		this.topicNameNumIdx = topicNameNumIdx;
		this.baseUrl = baseUrl;
		this.datasetName = datasetName;
		this.analysisName = analysisName;
		this.topicNameScheme = topicNameScheme;
	}

	public static Bijection<String> topicNameNumIdx(final YambaDatabase db, final String datasetName, final String analysisName, final String nameScheme) {
		final Bijection<String> idx = new Bijection<String>();
		try {
			final int analysisID = db.analysisID(datasetName, analysisName);
			final int nameSchemeID = db.topicNameSchemeID(analysisID, nameScheme);
			for(Integer topic_id : db.topicIDs(datasetName, analysisName)) {
				final int topicNum = db.topicNumber(topic_id);

				final String topicName = db.topicName(topic_id, nameSchemeID);
				idx.add(topicNum, topicName);
			}
		} catch(SQLException e) {
			e.printStackTrace();
		}
		return idx;
	}

	public String topicName(final int topicID) throws SQLException {
		final int analysisID = db.analysisID(datasetName, analysisName);
		final int nameSchemeID = db.topicNameSchemeID(analysisID, topicNameScheme);
		return db.topicName(topicID, nameSchemeID);
	}

	private void generateGraph(final Generator gtor) {
		System.out.println("generateGraph");

		final ProjectController pc = Lookup.getDefault().lookup(ProjectController.class);
		pc.newProject();
		final Workspace gephiWorkspace = pc.getCurrentWorkspace();

		Container container = Lookup.getDefault().lookup(ContainerFactory.class).newContainer();
		container.setReport(new Report());

		gtor.generate(container.getLoader());

		ImportController importController = Lookup.getDefault().lookup(ImportController.class);
		importController.process(container, new DefaultProcessor(), gephiWorkspace);
	}

	public void saveAsGexf(final String gexfFilename) {
		System.out.println("Save to file...");
		makeParentDirsFor(gexfFilename);
		final ExportController ec = Lookup.getDefault().lookup(ExportController.class);
		try {
			ec.exportFile(new File(gexfFilename));
		} catch (IOException ex) {
			ex.printStackTrace();
			return;
		}
	}

	private GraphModel currentModel() {
		return Lookup.getDefault().lookup(GraphController.class).getModel();
	}

	public void doLayout() {
		System.out.println("doLayout");
		AutoLayout autoLayout = new AutoLayout(1, TimeUnit.MINUTES);
		autoLayout.setGraphModel(currentModel());
		YifanHuLayout firstLayout = new YifanHuLayout(null, new StepDisplacement(1f));
		ForceAtlasLayout secondLayout = new ForceAtlasLayout(null);
		AutoLayout.DynamicProperty adjustBySizeProperty = AutoLayout.createDynamicProperty("Adjust by Sizes", Boolean.TRUE, 0.1f);//True after 10% of layout time
		AutoLayout.DynamicProperty repulsionProperty = AutoLayout.createDynamicProperty("Repulsion strength", new Double(12000), 0f);//500 for the complete period
		AutoLayout.DynamicProperty attractionProperty = AutoLayout.createDynamicProperty("Attraction strength", new Double(1.0), 0f);
		AutoLayout.DynamicProperty gravityProperty = AutoLayout.createDynamicProperty("Gravity", new Double(2000), 0f);
		autoLayout.addLayout(firstLayout, 0.5f);
		autoLayout.addLayout(secondLayout, 0.5f, new AutoLayout.DynamicProperty[]{adjustBySizeProperty, repulsionProperty, attractionProperty, gravityProperty});
		autoLayout.execute();
	}

	public void doColors() {
		System.out.println("doColors");
		//Rank color by Degree
		RankingController rankingController = Lookup.getDefault().lookup(RankingController.class);
		NodeRanking degreeRanking = rankingController.getRankingModel().getDegreeRanking();
		ColorTransformer colorTransformer = rankingController.getObjectColorTransformer(degreeRanking);
		colorTransformer.setColors(new Color[]{new Color(0xFCFFFD), new Color(0xFF9702)});
		rankingController.transform(colorTransformer);
	}

	public void doSizes() {
		AttributeModel attributeModel = Lookup.getDefault().lookup(AttributeController.class).getModel();
		RankingController rankingController = Lookup.getDefault().lookup(RankingController.class);

		//Get Centrality
		GraphDistance distance = new GraphDistance();
		distance.setDirected(true);
		distance.execute(currentModel(), attributeModel);

		//Rank size by centrality
		AttributeColumn centralityColumn = attributeModel.getNodeTable().getColumn(GraphDistance.BETWEENNESS);
		NodeRanking centralityRanking = rankingController.getRankingModel().getNodeAttributeRanking(centralityColumn);
		SizeTransformer sizeTransformer = rankingController.getObjectSizeTransformer(centralityRanking);
		sizeTransformer.setMinSize(10);
		sizeTransformer.setMaxSize(80);

		//Interpolator splines = new BezierInterpolator((float) control1.getX(),
		//(float) control1.getY(),
		//(float) control2.getX(), (float) control2.getY());
		//sizeTransformer.setInterpolator(splines);

		rankingController.transform(sizeTransformer);
	}

	public void exportTopicMapImages(final String imgDir, final String linkedImgDir) {
		System.out.println("Exporting images");

		new File(imgDir).mkdirs();
		new File(linkedImgDir).mkdirs();

		//Set up the preview:
		PreviewModel model = Lookup.getDefault().lookup(PreviewController.class).getModel();
		model.getNodeSupervisor().setShowNodeLabels(Boolean.TRUE);
		model.getGlobalEdgeSupervisor().setShowFlag(Boolean.FALSE);
		//ColorizerFactory colorizerFactory = Lookup.getDefault().lookup(ColorizerFactory.class);
		//model.getNodeSupervisor().setNodeColorizer((NodeColorizer) colorizerFactory.createCustomColorMode(Color.BLUE));
		//model.getUniEdgeSupervisor().setColorizer((EdgeColorizer) colorizerFactory.createCustomColorMode(Color.LIGHT_GRAY));
		//model.getBiEdgeSupervisor().setColorizer((EdgeColorizer) colorizerFactory.createCustomColorMode(Color.GRAY));
		//model.getUniEdgeSupervisor().setEdgeScale(0.1f);
		//model.getBiEdgeSupervisor().setEdgeScale(0.1f);
		model.getNodeSupervisor().setProportionalLabelSize(Boolean.FALSE);
		model.getNodeSupervisor().setBaseNodeLabelFont(model.getNodeSupervisor().getBaseNodeLabelFont().deriveFont(28f));

		FilterController filterController = Lookup.getDefault().lookup(FilterController.class);

		try {
			final TopicSVGLinker linker = new TopicSVGLinker(baseUrl, datasetName, analysisName, "#ff0000", topicNameNumIdx);
			Integer[] topicIDs = db.topicIDs(datasetName, analysisName).toArray(new Integer[0]);
			Arrays.sort(topicIDs);
			for(final int topicID : topicIDs) {
				final int topicNumber = db.topicNumber(topicID);
				final String topicNodeID = topicNodeID(topicNumber);

				final DistanceFilter filter = new DistanceFilter();
				filter.setPattern("^" + topicNodeID + "$");

				final GraphView view = filterController.filter(filterController.createQuery(filter));
				currentModel().setVisibleView(view);

				ExportController ec = Lookup.getDefault().lookup(ExportController.class);
				try {
					ec.exportFile(new File(imgDir + "/" + topicNodeID + ".svg"), ec.getExporter("svg"));
				} catch (IOException ex) {
					ex.printStackTrace();
					return;
				}

				final String svgFile = imgDir + "/" + topicNodeID + ".svg";
				final String linkedSvgFile = linkedImgDir + "/" + topicNodeID + ".svg";
				linker.createLinkedSVG(svgFile, linkedSvgFile, topicNumber);
			}
		} catch(SQLException e) {
			e.printStackTrace();
		}
	}

	static String topicNodeID(final int topicNumber) {
		//return "topic[" + topicNumber + "]";
		return String.valueOf(topicNumber);
	}

	static String edgeID(final int topic1_id, final int topic2_id) {
		return "edge[" + topic1_id + "," + topic2_id + "]";
	}

	private static void makeParentDirsFor(final String filePath) {
		final File file = new File(filePath);
		file.getParentFile().mkdirs();
	}

	public static void main(String[] args) {
		final int minValue = Integer.parseInt(args[0]);
		final String baseUrl = args[1];
		final String datasetName = args[2];
		final String analysisName = args[3];
		final String topicNameScheme = args[4];
		final String pairwiseMetricName = args[5];
		final String yambaFilename = args[6];
		final String imgDir = args[7];
		final String linkedImgDir = args[8];
		final String gexfFilename = args[9];

		System.out.println("TopicMapGraphBuilder");
		System.out.println("\tmin value: " + minValue);
		System.out.println("\tbase url: " + baseUrl);
		System.out.println("\tdataset name: " + datasetName);
		System.out.println("\tanalysis name: " + analysisName);
		System.out.println("\ttopic name scheme: " + topicNameScheme);
		System.out.println("\tpairwise topic metric: " + pairwiseMetricName);
		System.out.println("\tyamba file: " + yambaFilename);
		System.out.println("\timg dir: " + imgDir);
		System.out.println("\tlinked img dir: " + linkedImgDir);
		System.out.println("\tgexf file name: " + gexfFilename);

		final YambaDatabase db = new YambaDatabase(yambaFilename);
		final Bijection<String> topicNameNumIdx = topicNameNumIdx(db, datasetName, analysisName, topicNameScheme);
		final TopicMapGraphBuilder tmg = new TopicMapGraphBuilder(db, topicNameNumIdx, baseUrl, datasetName, analysisName, topicNameScheme);
		final TopicMetricDistanceGraphGenerator generator = new TopicMetricDistanceGraphGenerator(db, datasetName, analysisName, pairwiseMetricName, topicNameNumIdx);
		generator.setMinValue(minValue);
		tmg.generateGraph(generator);
		tmg.doColors();
		tmg.doSizes();
		tmg.doLayout();
		tmg.saveAsGexf(gexfFilename);
		tmg.exportTopicMapImages(imgDir, linkedImgDir);
	}
}
