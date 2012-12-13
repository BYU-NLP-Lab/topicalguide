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

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * WARNING: This class constructs queries in a horribly unsafe fashion that's begging for a SQL
 * injection attack. Need to use prepared statements with parameter substitution rather than
 * concatenating strings.
 * 
 * @author Josh Hansen
 *
 */
public class YambaDatabase {
	private final Connection connection;
	
	public YambaDatabase(final String jdbcPath) {
		this.connection = connect(jdbcPath);
	}
	
	private static String connectionClassName(final String jdbcPath) {
		if(jdbcPath.contains("sqlite")) {
			return "org.sqlite.JDBC";
		}
		if(jdbcPath.contains("mysql")) {
			return "com.mysql.jdbc.Driver";
		}
		throw new IllegalArgumentException("Unrecognized JDBC path type: " + jdbcPath);
	}
	
	private static Connection connect(final String jdbcPath) {
		Connection connection = null;
		try {
			Class.forName(connectionClassName(jdbcPath));
		} catch (ClassNotFoundException e) {
			e.printStackTrace();
		}
		
		try {
			connection = DriverManager.getConnection(jdbcPath);
		} catch(SQLException e) {
			e.printStackTrace();
			System.err.println("Couldn't connect to database at " + jdbcPath + ". Exiting.");
			System.exit(-1);
		}
		return connection;
	}

	/** For raw SQL access */
	public Connection connection() {
		return connection;
	}

	public int pairwiseMetricID(final String pairwiseMetricName, final int analysisID) throws SQLException {
		final String sql = "select id from visualize_pairwisetopicmetric where name='" + pairwiseMetricName + "' and analysis_id='" + analysisID + "';";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public int datasetID(final String datasetName) throws SQLException {
		final String sql = "select id from visualize_dataset where name='" + datasetName + "';";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public int analysisID(final String datasetName, final String analysisName) throws SQLException {
		final int datasetID = datasetID(datasetName);
		final String sql = "select id from visualize_analysis where name='" + analysisName + "' and dataset_id=" + datasetID + ";";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public int analysisIDfromPairwiseMetricName(final String pairwiseMetricName) throws SQLException {
		ResultSet rs = connection.createStatement().executeQuery("select analysis_id from visualize_pairwisetopicmetric where name='" + pairwiseMetricName + "';");
		rs.next();
		return rs.getInt("analysis_id");
	}

	public int topicID(final String datasetName, final String analysisName, final int topicNum) throws SQLException {
		final int analysisID = analysisID(datasetName, analysisName);
		final String sql = "select id from visualize_topic where number=" + topicNum + " and analysis_id=" + analysisID + ";";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public Set<Integer> topicIDs(final String datasetName, final String analysisName) throws SQLException {
		try {
			final int analysisID = analysisID(datasetName, analysisName);
			return Collections.unmodifiableSet(topicIDs(analysisID));
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return null;
	}

	public Set<Integer> topicIDs(final int analysisID) throws SQLException {
		Set<Integer> topicIDs = new HashSet<Integer>();

		final String sql = "select id as topic_id from visualize_topic where analysis_id=" + analysisID + ";";
		ResultSet rs = connection.createStatement().executeQuery(sql);
		while(rs.next())
			topicIDs.add(rs.getInt("topic_id"));

		return topicIDs;
	}

	public int topicNumber(final int topicID) throws SQLException {
		final ResultSet rs = connection.createStatement().executeQuery("select number from visualize_topic where id=" + topicID + ";");
		rs.next();
		return rs.getInt("number");
	}

	public double pairwiseMetricValue(final int topic1_id, final int topic2_id, final int metric_id) throws SQLException {
		final String sql = "select value from visualize_pairwisetopicmetricvalue where topic1_id=" + topic1_id + " and topic2_id=" + topic2_id + " and metric_id=" + metric_id + ";";
		ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getDouble("value") * 100;
	}

	public String wordType(final int wordID) throws SQLException {
		final String sql = "select type from visualize_word where id=" + wordID + ";";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getString("type");
	}

	public int topicMetricID(final String name, final int analysisID) throws SQLException {
		final String sql = "select id from visualize_topicmetric where name='" + name + "' and analysis_id=" + analysisID + ";";
		ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public int createTopicMetric(final String name, final int analysisID) throws SQLException {
		final String sql = "insert into visualize_topicmetric (name,analysis_id) values('" + name + "','" + analysisID + "');";
		connection.createStatement().executeUpdate(sql);
		return topicMetricID(name, analysisID);
	}

	public double topicMetricValue(final int topicID, final int metricID) throws SQLException {
		final String sql = "select value from visualize_topicmetricvalue where topic_id=" + topicID + " and metric_id=" + metricID + ";";
		return connection.createStatement().executeQuery(sql).getDouble("value");
	}

	public boolean topicMetricValueExists(final int topicID, final int metricID) {
		final String sql = "select count(*) as count from visualize_topicmetricvalue where topic_id=" + topicID + " and metric_id=" + metricID + ";";
		boolean result = false;
		try {
			ResultSet rs = connection.createStatement().executeQuery(sql);
			rs.next();
			result = rs.getInt("count") > 0;
		} catch (SQLException e) {
			e.printStackTrace();
		}
		return result;
	}

	public void setTopicMetricValue(final int topicID, final int metricID, final double value) {
		final String sql = topicMetricValueExists(topicID, metricID)
		? "update visualize_topicmetricvalue set value=" + value + " where topic_id=" + topicID + " and metric_id=" + metricID + ";"
		: "insert into visualize_topicmetricvalue (topic_id,metric_id,value) values('" + topicID + "','" + metricID + "','" + value + "');";

		try {
			connection.createStatement().executeUpdate(sql);
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}

	public int topicNameSchemeID(final int analysisID, final String nameSchemeName) throws SQLException {
		final String sql = "select id from visualize_topicnamescheme where analysis_id=" + analysisID + " and name='" + nameSchemeName + "';";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getInt("id");
	}

	public String topicName(final int topicID, final int nameSchemeID) throws SQLException {
		final String sql = "select name from visualize_topicname where topic_id=" + topicID + " and name_scheme_id=" + nameSchemeID + ";";
		final ResultSet rs = connection.createStatement().executeQuery(sql);
		rs.next();
		return rs.getString("name");
	}
}
