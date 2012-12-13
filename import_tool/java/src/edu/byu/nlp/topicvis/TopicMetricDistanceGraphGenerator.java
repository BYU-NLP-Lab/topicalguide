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

import java.sql.SQLException;
import java.util.Set;

import org.gephi.io.generator.spi.Generator;
import org.gephi.io.generator.spi.GeneratorUI;
import org.gephi.io.importer.api.ContainerLoader;
import org.gephi.io.importer.api.EdgeDraft;
import org.gephi.io.importer.api.NodeDraft;
import org.gephi.utils.progress.ProgressTicket;


public class TopicMetricDistanceGraphGenerator implements Generator {
	private double minValue = Double.NEGATIVE_INFINITY;
	private double maxValue = Double.POSITIVE_INFINITY;
	private final YambaDatabase db;
	private final String datasetName;
	private final String analysisName;
	private final String pairwiseMetricName;
	private final Bijection<String> topicNumToTopicName;

	public TopicMetricDistanceGraphGenerator(final YambaDatabase db, final String datasetName, final String analysisName, final String pairwiseMetricName, final Bijection<String> topicNumToTopicName) {
		this.db = db;
		this.datasetName = datasetName;
		this.analysisName = analysisName;
		this.pairwiseMetricName = pairwiseMetricName;
		this.topicNumToTopicName = topicNumToTopicName;
	}

	public void setMinValue(double minValue) {
		this.minValue = minValue;
	}

	public void setMaxValue(double maxValue) {
		this.maxValue = maxValue;
	}

	private NodeDraft ensureNode(final ContainerLoader container, final int topic_num) throws SQLException {
		final String topicID = TopicMapGraphBuilder.topicNodeID(topic_num);
		final NodeDraft topicNode = container.getNode(topicID);
		topicNode.setLabel(topicNumToTopicName.itemAt(topic_num));
		return topicNode;
	}

	@Override
	public void generate(ContainerLoader container) {
		try {
			final int analysisID = db.analysisID(datasetName, analysisName);
			final int metric_id = db.pairwiseMetricID(pairwiseMetricName, analysisID);

			final Set<Integer> topicIDs = db.topicIDs(datasetName, analysisName);
			for(Integer topic1_id : topicIDs) {
				final int topic1_num = db.topicNumber(topic1_id);
				for(Integer topic2_id : topicIDs) {
					final int topic2_num = db.topicNumber(topic2_id);
					if(topic1_id < topic2_id) {
						final String edgeID = TopicMapGraphBuilder.edgeID(topic1_id, topic2_id);

						EdgeDraft edge = container.getEdge(edgeID);
						if(edge == null) {
							final double metricValue = db.pairwiseMetricValue(topic1_id, topic2_id, metric_id);
							if(valueQualifies(metricValue)) {
								final NodeDraft topic1Node = ensureNode(container, topic1_num);
								final NodeDraft topic2Node = ensureNode(container, topic2_num);
								edge = container.factory().newEdgeDraft();
								edge.setSource(topic1Node);
								edge.setTarget(topic2Node);
								edge.setWeight((float) metricValue);

								edge.setId(edgeID);
								container.addEdge(edge);
							}
						}
					}
				}
			}
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}

	private boolean valueQualifies(final double value) {
		return value > minValue && value < maxValue;
	}

	@Override
	public String getName() {
		return this.getClass().getName();
	}

	@Override
	public GeneratorUI getUI() {
		return null;
	}

	@Override
	public boolean cancel() {
		return false;
	}

	@Override
	public void setProgressTicket(ProgressTicket progressTicket) {
	}
}