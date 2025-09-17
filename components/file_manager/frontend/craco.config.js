module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Preserve your existing fallback
      webpackConfig.resolve.fallback = {
        ...webpackConfig.resolve.fallback,
        crypto: false,
      };

      // Find the existing rule array that contains 'oneOf'
      const oneOfRule = webpackConfig.module.rules.find((rule) => Array.isArray(rule.oneOf)).oneOf;

      // Modify the default file-loader to exclude .svg
      const fileLoader = oneOfRule.find((rule) =>
        rule.test && rule.test.toString().includes('svg')
      );

      fileLoader.exclude = /\.svg$/;

      // Add a new rule using @svgr/webpack
      oneOfRule.unshift({
        test: /\.svg$/,
        use: [
          {
            loader: require.resolve('@svgr/webpack'),
            options: {
              icon: true,
            },
          },
        ],
      });

      return webpackConfig;
    },
  },
};